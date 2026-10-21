# Architecture

## Overview

```
 Browser
 ├── web client (React)  ── JSON ──►  /api/auth, /api/admin, /api/game
 └── Ruffle (Flash game) ── legacy ─►  /static/dragoncity/srv/*, /flash, /assets, /stream
                                          │
                                          ▼
                              Flask app (gunicorn, 1 process)
                              ├── auth/      sessions, CSRF/origin check
                              ├── api/       JSON API
                              ├── routes/    original game endpoints
                              ├── commands/  one module per packet command
                              └── game/      rules
                                   │                    │
                          PostgreSQL                 MongoDB
                          users, sessions            players, pvp_isle, pvp_players,
                                                     pending_assists
```

One origin serves everything: the web client (the built Vite app), the JSON API, and the
endpoints the Flash client expects. That is what lets the login cookie reach the Flash client's
requests and keeps CSRF protection simple.

## The two clients

**Web client** (`frontend/`): React + Vite + shadcn/ui. It handles sign-up, login, the admin
panel and the game page. The game page asks `GET /api/game/bootstrap` for the player's flash
variables, creates a Ruffle player and loads `flash/DCLoader.swf` with them.

**Flash client**, running inside Ruffle: it talks the original protocol (see
[game-protocol.md](game-protocol.md)). It has the original servers hardcoded, so the web client
gives Ruffle `urlRewriteRules` that send every request for `static.socialpointgames.com`,
`sp-translations.socialpointgames.com`, `graph.facebook.com`, ... to this server. This replaces
the old approach of editing the Windows `hosts` file.

## Identity

The player is always the logged-in account. The cookie `dc_session` identifies the session; the
account id (`users.id`, a number starting at 200,000,000) is also the in-game player id
(`fb_sig_user`). Ids the Flash client sends (`USERID`, `id`) are ignored.

Request pipeline (`auth/context.py`), for every request:

1. **Origin check** for `POST/PUT/PATCH/DELETE`: if the browser sends `Origin` (or `Referer`),
   it must match the request host or `ALLOWED_ORIGINS`; otherwise `403`.
2. **Load the user** from the cookie (`sessions` → `users`). Expired or disabled accounts are
   treated as logged out.
3. The view runs; `@login_required` / `@admin_required` enforce access.
4. Security headers are added (`nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, and
   `Cache-Control: no-store` for `/api/*`).

## Data

### PostgreSQL (SQLAlchemy, Alembic)

| Table | Columns |
|---|---|
| `users` | `id` (identity, starts at 200000000), `email` (unique, lower-case), `password_hash` (Argon2id), `is_admin`, `is_active`, `created_at`, `last_login_at` |
| `sessions` | `token_hash` (SHA-256 of the cookie token, primary key), `user_id` (cascade delete), `created_at`, `last_seen_at`, `expires_at`, `ip`, `user_agent` |

Schema changes go through migrations in `src/migrations/versions/`, applied by
`python -m src migrate` (the container does it on every start).

### MongoDB (pymongo)

| Collection | Documents |
|---|---|
| `players` | `_id` = player id; `data` = the save exactly as the Flash client sees it (`playerInfo`, `map`, `privateState`, ...); `kompu_offers` (per-player black-market offers, merged into the game config when served); `market` (the player's achievement-points market); `minigame_ts`; `created_at`, `updated_at`. |
| `pvp_isle` | `_id` = opponent id; `order`; `entry` = the row shown in the PvP league list. |
| `pvp_players` | `_id` = opponent id; `data` = the opponent's dragons and team. |
| `pending_assists` | `target`, `helper`, `clicks`, `at`: neighbour assists waiting to be merged into the target's save. |

The game configuration (items, levels, goals, ...) is **not** in a database: it is a large,
read-only file loaded once per process (`storage.load_base_config`). Only the black-market
offers differ per player.

## Request flow of `packet.php`

`POST /static/dragoncity/srv/packet.php` carries a batch of commands (`data=<signature>;<json>`;
the signature is ignored, its key ships in the SWF).

1. The route reads and validates the payload (size, JSON, no `NaN`).
2. It takes the **per-player lock**, loads the save (merging any queued assists), and builds the
   player's game config.
3. `dispatch_commands` runs each command:
   - looks up the handler (unknown commands get a generic `ok`);
   - takes a snapshot of the save;
   - validates the argument list, then calls the handler;
   - on `CommandRejected` or any exception it restores the snapshot and logs it;
   - appends the response entry with the player's resources after the command.
4. The save is written back, the lock released, and the player's event stream is told the game
   was saved.
5. The response is `<signature>;<json>` with one entry per command.

## Concurrency

- Read-modify-write cycles on a save run under `storage.player_lock(player_id)`.
- A neighbour's assist never edits another player's save: it is queued in `pending_assists` and
  merged when the target next loads their save. No two requests rewrite the same save at once.
- The lock, the SSE channels (`state.py`) and the rate limiter are **in process memory**, which
  is why the server runs a single gunicorn worker with many threads. See
  [deployment.md](deployment.md).

## Live "Saved" notifications

`GET /stream` is a Server-Sent Events stream, one per open game tab. After each saved packet
the server sends `JUEGO_GUARDADO`; the web client shows a short "Saved" hint in the header. A
`PING` is sent every 20 seconds to keep the connection open. The literal `JUEGO_GUARDADO` is
kept from the original client; it is the `SseEvent.GAME_SAVED` enum.

## Code organisation

| Package | Responsibility |
|---|---|
| `commands/` | One module per command; `base.py` holds the registry and `CommandContext`; `validation.py` the argument checks; `dispatcher.py` the loop above. |
| `game/` | Rules shared by commands and routes: `breeding`, `black_market`, `market`, `pvp`, `inventory`, `dragonarium`, `training`, `combat`, `map_items`, `levels`, `items`. |
| `storage.py` | The only place that talks to the player collections and the config file. |
| `enums.py` | `Command`, `SseEvent`, `SrvEndpoint`, `Resource`, `GroupType`, `DragonAttribute`, `DragonariumTab`, `OfferType`. |
| `routes/` | The original endpoints (`srv`, `packet`, `market`, `minigames`, game files, the web client). |
| `api/` | The JSON API (`auth`, `admin`, `game`). |

## Design decisions

- **Validate everything, trust nothing from the client.** Handlers read arguments only through
  `ctx.int_arg`, `ctx.uid_arg`, `ctx.iso_arg`, `ctx.text_arg`, ... and charge through
  `ctx.pay()`. See [SECURITY.md](SECURITY.md).
- **A failed command is a no-op.** The save is restored from a snapshot, so a half-applied
  command can never reach the database.
- **The save keeps the client's shape.** `data` is the JSON the Flash client already knows, so
  handlers are a close port of the original logic; a small normaliser fixes the shapes PHP got
  wrong in the captured template (empty arrays that should be objects).
- **One origin.** Simplifies cookies and CSRF, and lets the Flash client authenticate with the
  same cookie.
- **Passwords with Argon2id and sessions stored as hashes**: a database leak does not leak
  logins.
