# Roadmap: tasks and ideas

Things we want to do but have not started. Add new ideas at the bottom of "Ideas".

## Ideas

### Friend system

**Goal:** a player sends a friend request to another player by id, and the other player can
accept (or decline) it. The Flash client was never built for this, so the whole flow lives in
our web client; the game only sees the result (neighbours).

**Done (first step):** the `friendships` table, administrators adding/removing friends
(`/api/admin/users/{id}/friends` and the "Friends" section of the Manage dialog), the game
side (`fb_sig_friends`, the `neighbors` list in `get_player_info`, visiting) and the friend-only
restriction on visits and `assist_neighbor`. Verified in the real client: a friend appears in the
neighbours bar and *Visit* opens their island. How the client uses neighbours is documented in
[game-protocol.md](game-protocol.md#neighbours).

**Still to do:** the request/accept flow and its web pages. Sketch:

- **Data:** `friendships` already has `requester_id`, `status` (`pending` / `accepted`),
  `created_at` and `responded_at`, with the pair stored once. The request flow only needs to
  create `pending` rows and flip them to `accepted` (the game ignores anything not accepted).
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
- **Game integration:** done, see above. Possible extras: *Send gift* (a command the server
  does not implement yet) and a friends cap (the client mentions up to 170 friends).
- **Privacy:** requests go by player id, so ids are effectively public handles; show the
  player's name but never the email, and let players block or ignore requests.
- **Tests:** request/accept/decline flows, duplicates and self-requests, ids that do not
  exist, removing a friend, that a stranger cannot assist or visit when restricted, and that
  one player cannot answer another player's request.

## Tasks

- [ ] Import the old JSON saves (`web/srv/<id>/<id>.json`) into accounts, if anyone wants to
  keep progress from before the move to MongoDB.
