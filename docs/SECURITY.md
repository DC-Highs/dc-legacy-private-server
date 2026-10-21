# Security notes

The Flash client is untrusted code running on the player's machine: anyone can replay,
edit or forge the requests it sends. The original server believed whatever the client said.
This document lists what that allowed, how the server handles it now, and what cannot be
fixed without simulating the game on the server.

## Threat model

- **A player who edits packets** to get gold, gems, food, xp, dragons or achievement points they
  did not earn, or to act on someone else's save.
- **A visitor without an account** who tries to read or change anything.
- **A malicious website** that makes a logged-in player's browser send requests (CSRF).
- **Large or odd input** meant to break the save or exhaust the server.

Out of scope: someone with access to the host, the databases or the `.env` file.

## Vulnerabilities of the original server and their fixes

### Identity and access

| Problem | Fix |
|---|---|
| The player id came from the request (`USERID`, `id`, `user_id`, `fb_sig_user`): anyone could play, read or **delete** any account. | Identity comes only from the login session. Client-sent ids are ignored (`routes/srv.py`, `routes/packet.py`). |
| `user_id` was joined into a file path (`web/srv/<id>/`): `../` reached other directories and `/delete_profile` could `rmtree` them. | Saves live in MongoDB under an integer `_id`; there are no paths built from client input. `/delete_profile` is gone (admins delete users). |
| `/delete_profile`, `/generate_pvp`, the market and minigame endpoints needed no login. | Every game endpoint requires a session; PvP generation is admin-only. |
| Visiting an unknown neighbour created a new save for that id, and any player's save could be read by anyone. | Visiting is read-only and only possible for **friends** (404 otherwise), plus Deus, the system account the game shows to everybody. |
| Game files (`/flash`, `/assets`) were public. | They require a login. |
| Wildcard CORS (`Access-Control-Allow-Origin: *`). | CORS is not enabled; the client and API share one origin. |
| `str(exception)` returned to the client. | Generic 500 body; details go to the log. |

### Accounts and sessions

- Passwords: Argon2id, 8–128 characters, confirmation required at sign-up. Verification runs
  against a dummy hash when the email is unknown, and the error is the same for a wrong
  password and an unknown email (no user enumeration through login).
- Sessions: 256-bit random token in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` when
  `COOKIE_SECURE=true`); only the SHA-256 of the token is stored. Logging in creates a new
  token (no fixation). Disabling an account or changing its password ends its sessions.
- CSRF: `SameSite=Lax` plus an `Origin`/`Referer` check on every state-changing request
  (cross-site and `Origin: null` are refused).
- Rate limits: login (5/min, 20/h), sign-up (3/min, 10/h), packets (600/min per account).
- Request bodies are capped (1 MB; packets 256 KB); `NaN`/`Infinity` are rejected.
- Admin API: admin-only, cannot disable, demote or delete yourself, search escapes `LIKE`
  wildcards, all fields are validated (unknown fields are refused: no mass assignment).
- SQL injection: SQLAlchemy with bound parameters only. NoSQL injection: queries use integer
  ids from the session; client JSON is never used as a query, and `$`/`.` keys in client JSON
  are rejected before storage.

### Resource injection through `packet.php`

Every command now validates its arguments (`commands/validation.py`): integers must be real
integers in a sane range (no strings, floats, booleans, huge numbers or objects), text is
length-limited, ids must refer to things the player owns, and a packet is limited to 200
commands of at most 16 arguments. A rejected command changes nothing; an unexpected error
rolls the whole command back (the save is restored from a snapshot).

| Exploit in the original | Now |
|---|---|
| `collect` with a client-chosen gold amount (infinite gold). | Capped by what the dragons in that habitat could have produced; only habitats pay gold. |
| `buy`, `buy_egg`, `activate`, `expand_island`, `kompu_*`, `dragonarium_add`, `deus_cards_generate` charged with `max(0, ...)` or not at all: free items, expansions and draws, even negative balances. | `ctx.pay()` rejects the command when the player cannot afford it. |
| Items with no price (`costs` missing) and dragons could be "bought" through `buy` for free. | Only priced, non-dragon items can be bought; eggs only for priced dragons; level requirements are enforced. |
| `place_stored_dragon`, `dragonarium_place_stored` created any dragon at any level when it was not in storage ("forcing its creation"). | The dragon must be in storage/gifts; its level comes from storage, not from the client. |
| `breed_dragon` with unknown parents returned a free Terra dragon. | Both parents must exist and differ. |
| `level_up` accepted any level and paid its reward again on every call. | One level at a time, and the XP for that level is required. |
| `complete_goal` could be claimed forever. | Each goal pays once. |
| `finish_building` paid the build XP on every call. | Only objects under construction can be finished. |
| `weekly_reward` could be claimed again and again. | At most once every 5 days. |
| `deus_cards_generate`/`claim`: unlimited free draws and re-rolls; claim without a draw. | One free draw per 24 h (or after the "retry" prize), consumed at draw time; claim only for a server-generated prize, once. |
| `end_tournament`, `end_attack_f`: results could be reported without a fight, repeatedly. | A tournament must have begun; a PvP fight must have been started with `attack_player` against a real opponent, last 10 s–1 h, and is consumed when reported. |
| `assist_receive` paid 10 xp + resources per call without limit; `assist_neighbor` appended unbounded data to anyone's save. | Assists are queued (size-limited, only to friends, not yourself) and each `assist_receive` consumes one real click. |
| `complete_collection` did not check the dragons. | The player must own every dragon of the collection. |
| `collect fc` harvested crops before they grew. | The crop must have grown (`speed_collect` still works). The tutorial gets one early harvest because the client replays it in a single packet. |
| `finish_training` was instant; `speed_training` taught the attack even when the gems were missing and priced it wrongly (integer key vs text key in the config). | Training must have run its time; `speed_training` charges the real price and requires the gems. |
| `set_goals`, `start_training`, `set_attack_team`, `set_help_map`… grew lists to any size (memory/DoS, and the 16 MB document limit). | Indexes, list sizes and key counts are bounded. |
| Client-chosen egg/dragon ids could collide and shadow existing ones. | New ids must be unused. |
| Dragonarium storage had no capacity limit. | The tab's slot count is enforced. |

### Reliability fixes found on the way

- Saves are changed under a per-player lock, and neighbour assists are queued instead of
  rewriting another player's save, so concurrent requests cannot lose updates.
- The captured player template had PHP-style empty arrays where the code expects objects
  (`map.store`, `kompuBoxesOpened`…); it is normalised when a save is created or loaded.
- `get_player_info` no longer fails for a player who has never unlocked the black market.

### Friends and the 5-gem reward

- Requests are authenticated and validated (no self, unknown or disabled accounts), rate
  limited (30/hour per account) and capped (5 pending sent requests and 20 friends by default,
  `MAX_PENDING_REQUESTS` and `MAX_FRIENDS`); a declined sender waits 7
  days. Only the receiver can accept or decline, only the sender can cancel. Responses never
  contain emails.
- The reward is paid by the server, to both sides, only for the first 5 friends of each player
  and once per friend (also after removing and re-adding). It is not a client command, so a
  modified client cannot ask for it.
- **Known limit:** nothing stops one person from creating several accounts and befriending
  them to collect 5 × 5 gems per account. Sign-up is rate limited (3 per minute and 10 per hour
  per address), but if that matters, set `REGISTRATION_ENABLED=false` and create accounts by
  hand, or lower `FRIEND_REWARD_LIMIT` in `src/friends.py`.

## What the server cannot verify

These are inherent to a client that simulates the game by itself:

- **Timers of buildings, hatching and breeding.** The commands that speed them up with gems
  (`speed_building`, `speed_breeding`…) are not implemented, so enforcing the timers would
  break legitimate play. A modified client can therefore finish buildings, eggs and
  breedings early. Crop and training timers *are* enforced because their speed-up commands exist.
- **Fights.** The server does not simulate combat: a modified client can report victories
  (rate-limited by the minimum fight time and by one reported result per `attack_player`).
- **Minigame rewards** are bounded (3 gems, once per minute per account) rather than verified.
- **`upgrade`** does not charge anything (as in the original); it is not a client-side
  injection, but it is free for everyone.
- **Habitat gold** is bounded by an estimate (coins per minute × elapsed time × 2) because the
  exact in-game formula is not known to the server. If legitimate collections are clipped, the
  server logs `claimed ... but at most ... was produced`; adjust `GOLD_TOLERANCE` in
  `commands/collect.py`.

## Operations checklist

- Use long random values for `POSTGRES_PASSWORD`, `MONGO_PASSWORD` and `ADMIN_PASSWORD`, and
  change the admin password after the first login if it was left in `.env`.
- Serve over HTTPS (`COOKIE_SECURE=true`, `TRUST_PROXY=true`); do not publish the database ports.
- Set `REGISTRATION_ENABLED=false` if the server should not accept new sign-ups.
- Watch the log for `Rejected ...` lines: repeated rejections from one player are a modified
  client (or a gap in the server that rejects something legitimate: please report it).
- The `SECRET_KEY` in `config.py` signs game packets and ships inside the SWF; it is not a secret.
