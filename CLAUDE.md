# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A server that replaces the original Dragon City (Flash) back end, plus a web client that runs the unmodified SWF in the browser with Ruffle. Flask + PostgreSQL (accounts/sessions) + MongoDB (player saves), packaged with Docker Compose. Docs for humans are in `README.md` and `docs/` (deployment, configuration, architecture, API, game protocol, development, SECURITY.md); don't duplicate them here.

## Commands

```bash
poetry install
poetry run pytest                              # whole suite, needs no services
poetry run pytest tests/test_game_security.py::test_a_goal_pays_out_once   # one test
poetry run python -m src <migrate|create-admin|seed|serve>        # CLI (serve = dev server on :8080)

cd frontend && npm install
npm run dev        # Vite on :5173, proxies /api /static /flash /assets /deploy /stream to :8080
npm run build      # tsc -b && vite build -> frontend/dist (served by Flask)
npm run lint       # oxlint

docker compose up -d --build                   # needs .env (copy .env.example)
```

Tests use SQLite (in memory) and `mongomock` (`tests/conftest.py`); helpers: the `player`/`admin_client` fixtures, `packet(client, ("cmd", [args]))`, `edit_save()` to set up a scenario. The web client has no tests.

Migrations: edit `src/db/models.py`, autogenerate with Alembic against a real PostgreSQL (`src.cli._alembic_config()`), and strip the `sqlite` type variants from the generated file. `alembic.command.check` must report no diff. The container applies migrations on every start.

## Architecture (the parts that span files)

- **One origin serves everything**: the built SPA, `/api/*` (JSON API for the web client/admin) and the original Flash endpoints (`/static/dragoncity/srv/*`, `/flash`, `/assets`, `/stream`). The login cookie (`dc_session`) is what authenticates the Flash client's requests, so the `routes/pages.py` SPA catch-all must stay registered last (`routes/__init__.py`), and Vite's `assetsDir` is `_app` so it doesn't collide with the game's `/assets`.
- **Identity comes only from the session** (`auth/context.py`: origin/CSRF check, then user load). Ids the Flash client sends (`USERID`, `id`) are ignored on purpose. Player id == `users.id`.
- **`packet.php` flow**: `routes/packet.py` → takes `storage.player_lock(player_id)` → `commands/dispatcher.py` runs each command against a snapshot of the save, restoring it on `CommandRejected` or any exception → save written back → SSE `JUEGO_GUARDADO` sent. Unknown/rejected commands still answer `"ok"` so the client keeps running.
- **Commands**: one module per command in `src/commands/`, auto-discovered by `@command(Command.X)` (wire names live in `enums.py`). The save (`ctx.player_data`) keeps the Flash client's JSON shape; handlers are near-ports of the original logic.
- **Storage**: `storage.py` is the only module that touches the `players` collection and the read-only game config (`web/srv/get_game_config.json`, may start with `<signature>;`). Per-player black-market offers are merged into the config when served. A neighbour's assist is queued in `pending_assists` and merged on the target's next load instead of rewriting their save.
- **Neighbours = friendships** (`friends.py`, PostgreSQL `friendships`): `get_player_info` adds a computed `neighbors` list (never stored in the save), `/api/game/bootstrap` builds `fb_sig_friends` from it, and visiting (`user=<id>`) and `assist_neighbor` are friends-only. The client's own `neighbors` request field is ignored. Protocol details are in `docs/game-protocol.md#neighbours`; requests (`api/friends.py`) become `accepted` friendships, and `friends.award_both` pays the "add a friend, get 5 gems" reward (first 5 friends, once per friend) straight into the Mongo save.
- **Deus** (`system_accounts.py`): the client's built-in "Deus" card visits the fixed id `DEUS_PLAYER_ID` (100000030). A disabled system account + save is created at start-up and is the only non-friend that can be visited; without it the client hangs on a progress bar.
- **Single process on purpose** (`docker/gunicorn.conf.py`): per-player locks, SSE channels and the rate limiter are in memory. Don't add workers/replicas without moving those to a shared store.
- **Ruffle integration** (`frontend/src/components/game/ruffle.ts`): the SWF has the original hosts hardcoded, so Ruffle gets `urlRewriteRules` built from `legacyHosts` (`api/game.py`) that send them to this server; flash variables come from `GET /api/game/bootstrap`.

## Rules that must hold when touching commands

The client is untrusted (see `docs/SECURITY.md`). In a command: read arguments only through `ctx.int_arg/uid_arg/iso_arg/flag_arg/text_arg` (not `ctx.args[i]`), validate before mutating, charge with `ctx.pay()` (never `max(0, ...)`), take rewards from config/server state rather than client values, use `ctx.new_uid` for client-chosen ids, and `reject("...")` on anything wrong. Real client behaviour matters: the tutorial replays many commands in a single packet, so server-time checks between commands of one packet are unreliable (see `commands/collect.py`'s one-time tutorial harvest exception).

## Conventions specific to this repo

- Logs use `logging` in English, never `print`. API error messages are English too.
- The frontend follows the project's shadcn rules: add components with `npx shadcn@latest add <name>` (don't hand-write primitives), forms use `Controller` + `Field` + a zod schema (types named `{Name}FormValues`), text goes through `Typography`, body links through `@/components/ui/link`, components are `const X: FC<Props>`, and types are imported with `import type`. `cn` is implemented with `clsx` + `tailwind-merge` in `src/lib/utils.ts`.
- Game files (`flash/`, `assets/`, `domains/`) are not in the image and not under the MIT license; they are mounted read-only by `compose.yaml`. `.env` is git-ignored.
- Commit messages end with the `Co-Authored-By: Claude ...` trailer requested for this repo's commits.
