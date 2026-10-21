# Roadmap: tasks and ideas

Things we want to do but have not started. Add new ideas at the bottom of "Ideas".

## Ideas

### Friend system

**Goal:** a player sends a friend request to another player by id, and the other player can
accept (or decline) it. The Flash client was never built for this, so the whole flow lives in
our web client; the game only sees the result (neighbours).

**Feasible?** Yes. Sketch:

- **Data (PostgreSQL):** a `friendships` table: `requester_id`, `addressee_id`, `status`
  (`pending` / `accepted`), `created_at`, `responded_at`. Unique on the (unordered) pair, both
  ids reference `users`, and a player cannot befriend themselves. Add an Alembic migration.
- **API** (`api/friends.py`, login required, same CSRF/rate-limit rules as the rest):
  - `POST /api/friends/requests` `{playerId}` – send a request (rate-limited; reject unknown
    ids, yourself, existing friends and duplicate or reverse pending requests; if the other
    player already asked you, accept instead).
  - `GET /api/friends` – friends, plus incoming and outgoing pending requests.
  - `POST /api/friends/requests/{id}/accept` and `/decline`; `DELETE /api/friends/{playerId}`
    to remove a friend; maybe a "cancel my request" too.
- **Web client:** a "Friends" page (or dialog) from the header: my player id with a copy
  button, a field to send a request by id, incoming requests with Accept/Decline, the friend
  list with Remove, and a badge in the header when there are pending requests.
- **Game integration (the part to investigate first):**
  - The Flash client reads neighbours from `neighbors` in the player save and from the
    `fb_sig_friends` flash variable (hardcoded to `100000030` today). Build both from the
    accepted friendships, and check how the client shows and visits them.
  - Visiting a neighbour (`get_player_info.php?user=...`) is open to any existing player
    today; restrict it to friends if we want it to be private.
  - `assist_neighbor` could require an accepted friendship, which also limits abuse
    (see `docs/SECURITY.md`).
- **Privacy:** requests go by player id, so ids are effectively public handles; show the
  player's name but never the email, and let players block or ignore requests.
- **Tests:** request/accept/decline flows, duplicates and self-requests, ids that do not
  exist, removing a friend, that a stranger cannot assist or visit when restricted, and that
  one player cannot answer another player's request.

## Tasks

- [ ] Import the old JSON saves (`web/srv/<id>/<id>.json`) into accounts, if anyone wants to
  keep progress from before the move to MongoDB.
