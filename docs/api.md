# JSON API

Used by the web client and the admin panel. Everything is JSON over the same origin as the
page. The Flash client's own endpoints are in [game-protocol.md](game-protocol.md).

## Conventions

- **Authentication:** the `dc_session` cookie (`HttpOnly`, `SameSite=Lax`). There are no tokens
  to copy: log in, and the browser keeps the cookie.
- **State-changing requests** (`POST`, `PATCH`, `DELETE`) are refused with `403` when the
  browser's `Origin`/`Referer` is another site.
- **Bodies** must be JSON objects. Unknown fields are rejected (`400`), so you cannot set
  fields that are not part of the endpoint.
- **Errors** share one shape:

  ```json
  { "error": { "code": "validation_error", "message": "Some fields are invalid",
               "fields": { "email": "Invalid email: ..." } } }
  ```

  | Status | `code` | Meaning |
  |---|---|---|
  | 400 | `validation_error` | A field is invalid; `fields` says which. |
  | 401 | `unauthorized` / `invalid_credentials` | Not logged in / wrong email or password. |
  | 403 | `forbidden`, `account_disabled`, `registration_disabled` | Not allowed. |
  | 404 | `not_found` | Unknown user or save. |
  | 409 | `conflict` | The email is already registered. |
  | 413 | `payload_too_large` | Request or packet too big. |
  | 429 | `too_many_requests` | Rate limit hit. |
  | 500 | `internal_error` | Unexpected error (details only in the server log). |

## Types

```ts
type User = {
  id: number            // also the in-game player id
  email: string
  isAdmin: boolean
  isActive: boolean
  createdAt: string | null
  lastLoginAt: string | null
  playerName?: string   // only on /api/auth/* responses
  player?: {            // only on admin responses
    name: string; level: number; gold: number; cash: number; food: number; xp: number; dragons: number
  }
}
```

## Auth (`/api/auth`)

| Method and path | Body | Result |
|---|---|---|
| `POST /register` | `{ email, password, confirmPassword }` | `201 { user }` and the session cookie. |
| `POST /login` | `{ email, password }` | `200 { user }` and a new session cookie. |
| `POST /logout` | – | `200 { ok: true }`; the session is deleted and the cookie cleared. |
| `GET /me` | – | `200 { user }`, or `401`. |

Rules: the email is validated and lower-cased; the password has 8–128 characters and must differ
from the email; `confirmPassword` must match. Registering creates the game save. Login and
sign-up are rate limited (login 5/min and 20/h, sign-up 3/min and 10/h per client address). A
failed login never says whether the email exists.

## Game (`/api/game`)

| Method and path | Auth | Result |
|---|---|---|
| `GET /bootstrap` | login | `{ playerId, playerName, loader, servicesPath, flashVars, legacyHosts }`: everything the web client needs to start Ruffle. |
| `GET /health` | none | `200 { status: "ok" }` when PostgreSQL and MongoDB answer. Used by the Docker health check. |

## Admin (`/api/admin`)

All admin endpoints require an administrator (`401` when logged out, `403` otherwise).

| Method and path | Body / query | Result |
|---|---|---|
| `GET /users` | `query` (email substring or exact id), `page` (1), `pageSize` (20, max 100) | `{ items: User[], total, page, pageSize }`, newest first, each with `player`. |
| `POST /users` | `{ email, password, isAdmin? }` | `201 { user }`; also creates the game save. |
| `GET /users/{id}` | – | `{ user }` with `player`. |
| `PATCH /users/{id}` | any of `{ email, password, isAdmin, isActive }` | `{ user }`. Changing the password or disabling the account ends the user's sessions. |
| `DELETE /users/{id}` | – | Deletes the account, its sessions and its save. |
| `POST /users/{id}/reset-player` | – | Replaces the save with a fresh one. |
| `PATCH /users/{id}/resources` | any of `{ gold, cash, food }` (0 – 2,000,000,000) | Sets those resources in the save. |
| `GET /users/{id}/friends` | – | `{ items: [{ id, email, playerName }] }`, oldest friendship first. |
| `POST /users/{id}/friends` | `{ friendId }` | Makes two accounts friends (mutual); `201 { items }`. `400` for yourself, `404` unknown id, `409` already friends. |
| `DELETE /users/{id}/friends/{friendId}` | – | Ends the friendship; `{ items }`, `404` if they were not friends. |
| `POST /pvp/generate` | – | Adds 8 random PvP opponents; `{ totalOpponents }`. |

Safeguards: you cannot disable, demote or delete **your own** account; the search treats `%`
and `_` literally; the email must be unique (`409`).

## Other endpoints kept from the original

They have no web page but still work, and they act on the logged-in player:

| Method and path | Body | Notes |
|---|---|---|
| `GET /market_data` | – | The achievement-points market: points, offers, seconds to refresh. |
| `POST /market/redeem` | `{ "offer_id": 1..1000 }` | Spends points on an offer (once per offer; errors `400`/`404`). |
| `POST /minigame/reward` | `{ "gems": 0..3 }` | Adds gems; at most once per minute per account (`429`). |
