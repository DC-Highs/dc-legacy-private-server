# Game protocol

What the original Flash client expects from the server, and how this server answers. All of
these endpoints act on the **logged-in account** (cookie); ids sent by the client are ignored.
For the JSON API of the web client see [api.md](api.md).

## Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET/POST /static/dragoncity/srv/get_game_config.json` (or `.php`) | login | The game configuration as `<signature>;<json>`, with the player's own black-market offers. |
| `GET/POST /static/dragoncity/srv/get_player_info.json` (or `.php`) | login | The player's save, signed, with the `neighbors` list added (see [Neighbours](#neighbours)). With `user=<id>` it returns a **friend's** save, read-only (`404` for anyone who is not a friend). For the player's own island it also refreshes the black market. |
| `GET/POST /static/dragoncity/srv/get_pvp_isle.json`, `.php`, `get_pvp_isle_info.php` | login | A page (8) of PvP opponents; `?level=N` (1–1000). |
| `POST /static/dragoncity/srv/packet.php` | login | The batch of commands. See below. |
| `GET /stream` | login | Server-Sent Events: `JUEGO_GUARDADO` after each saved packet, `PING` every 20 s. |
| `GET /flash/<file>`, `/assets/<file>` | login | The SWF files and the game's assets. |
| `GET /deploy/dc/canvas/prod/<file>` | login | Translation files. |
| `GET /crossdomain.xml`, `/__utm.gif`, `/ga.js`, tracking stubs | none | Static answers for requests the client still makes. |
| other `/static/dragoncity/srv/<name>` | login | `{"result": "200"}`. |

Responses that carry data are signed: `HMAC-SHA256(SECRET_KEY, json)` as hex, then `;`, then the
compact JSON. The key is in `config.py`; it ships inside the SWF.

## Neighbours

How the Flash client gets and shows its friends (found by reading the SWF's ActionScript):

1. The page starts the game with the flash variable `fb_sig_friends`: the ids of the player's
   friends, comma separated. `GET /api/game/bootstrap` builds it from the friendships of the
   account (empty when there are none).
2. The client sends those ids to the server in `get_player_info` as the form field `neighbors`.
   The server **ignores** it (the client is untrusted) and uses the friendships it stores.
3. The response carries `neighbors`: one entry per friend,

   ```json
   { "pid": "200000012", "name": "bob", "xp": 0, "level": 1, "world_id": 0 }
   ```

   The client draws them in the bar at the bottom of the island (name, level star, xp).
4. Clicking a neighbour opens a menu with **Visit** and **Send gift**. *Visit* calls
   `get_player_info` with `user=<id>` and shows that player's island (read-only) with a
   "Return home" button. The **Assist** button sends `assist_neighbor`.

Friendships are mutual. Players make them with friend requests in the web client
([api.md](api.md#friends-apifriends)); administrators can also create them. `neighbors` is
computed on every request and is never stored in the save. Visiting and `assist_neighbor` are
refused for anyone who is not a friend.

**"Add a friend and get 5 gems."** The game's neighbour cards promise it. When a friendship is
made (a request accepted, or an administrator adding one) **both players** get 5 gems, for
each of their first 5 friends: one per invite card. A given friend pays once, even if the
friendship is ended and made again. The gems are added to the save on the spot; an open game
shows them after the next packet or a reload.

## `packet.php`

Request: form field `data` = `<signature>;<json>` (the signature is ignored), where the JSON is

```json
{ "commands": [ { "cmd": "buy", "args": ["700", 16, 3, 3, 0, 0, 1], "number": 1 } ] }
```

Limits: 256 KB for `data`, 200 commands per packet (extra ones are dropped), 16 arguments per
command, JSON no deeper than 3 levels, no `NaN`/`Infinity`. 600 packets per minute per account.

Response:

```json
{ "result": true,
  "response": [ { "result": "ok", "number": 1, "cmd": "buy",
                  "resources": { "pu": { "gold": 1900, "cash": 8, "food": 140, "xp": 100 } },
                  "error": null } ],
  "ts": 1792605861, "publishActions": 0 }
```

- `result` is `"ok"` unless the command returns something (breeding returns the dragon id,
  `attack_player` the enemy units, ...).
- `resources.pu` is the player's gold, gems, food and xp **after** that command.
- A command that is unknown, rejected by validation or that fails is answered with `"ok"` and
  the unchanged resources: the client keeps running and the save is not touched. The reason is
  in the server log (`Rejected <cmd> from player ...`).
- The client may send several commands in one packet (the tutorial replays everything it did in
  a single one), so the server cannot rely on the time between two commands of the same packet.

## Commands

60 of the 104 commands the client can send are implemented; the rest get the generic `ok`. Each
lives in `src/commands/<name>.py`. Arguments are listed in order. "Needs" is what
the server checks before changing anything.

### Buildings and the map

| Command | Arguments | What it does / needs |
|---|---|---|
| `buy` | iso id, item id, x, y, parent, frame, flag | Places a priced, non-dragon item. Needs the money (`pay`), an unused iso id and the item's minimum level. |
| `move` | iso id, x, y, frame | Moves an object of the map. |
| `orient` | iso id, frame | Rotates an object. |
| `store_item` | iso id | Moves an object into the warehouse. |
| `place_stored_item` | iso id, item id, x, y | Takes an item out of the warehouse onto the map. |
| `sell` | iso id, reason | Sells an object for its `sell_price`. |
| `sell_stored_item` | item id | Sells one item from the warehouse. |
| `activate` | iso id, crop | Plants a crop on a farm (pays the crop price; `0` clears it) or clears an obstacle (pays its cost). |
| `collect` | iso id [, gold or `"fc"`] | Habitat: collects gold (capped by what the dragons produced). Farm `"fc"`: harvests a grown crop (food and xp). |
| `speed_collect` | iso id, type | Pays gems to finish a crop's timer. |
| `finish_building` | iso id, flag | Completes an object under construction and pays its xp, once. |
| `upgrade` | iso id | Upgrades an object to the next type (`upgrades_to`). |
| `expand_gold`, `expand_cash` | expansion id | Buys the next island expansion with gold or gems. |
| `expand_island` | expansion id, cost index | Expands the island using `ISLANDS_COSTS`. |

### Dragons, eggs and breeding

| Command | Arguments | What it does / needs |
|---|---|---|
| `buy_egg` | egg uid, dragon id | Buys an egg of a priced dragon. The uid must be unused. |
| `hatch_egg` | egg uid, _, habitat iso, name | Hatches an egg into a habitat; adds the dragon to the dragon book. |
| `speed_hatch` | egg uid | Pays gems (1 per started hour) to finish an egg's timer. |
| `feed_dragon` | dragon uid | Feeds a dragon (food cost by level); raises its xp. |
| `rename_dragon` | dragon uid, name | Renames a dragon (≤ 32 characters). |
| `move_dragon` | dragon uid, habitat iso | Moves a dragon to another habitat. |
| `breed_dragon` | cave iso, parent 1, parent 2, use gems | Starts breeding two different dragons; may pay for the rarity boost. Returns the result dragon id. |
| `finish_breeding2` | cave iso, new egg uid, hatchery iso | Turns a finished breeding into an egg. |
| `sell_egg`, `sell_dragon` | uid | Sells an egg / a dragon on the map. |
| `place_stored_egg` | egg uid, dragon id, is gift | Takes an egg from the warehouse into the hatchery. |
| `place_stored_dragon` | uid, habitat iso, name, dragon id, level, is gift | Takes a stored dragon onto the map. The dragon must be in storage; its level comes from there. |
| `sell_stored_dragon` | dragon id, level, is gift | Sells a stored dragon. |

### Dragonarium

| Command | Arguments | What it does / needs |
|---|---|---|
| `dragonarium_push` | dragon uid | Moves a dragon into its tab (needs a free slot). |
| `dragonarium_pull` | _, tab, position, habitat iso | Takes a dragon out into a habitat. |
| `dragonarium_place_stored` | name, dragon id, level, is gift | Moves a stored dragon straight into the dragonarium. |
| `dragonarium_add` | tab | Buys one more slot for a tab (2–5 gems, up to 50 slots). |

### Progress, goals and rewards

| Command | Arguments | What it does / needs |
|---|---|---|
| `level_up` | level | Goes up exactly one level; needs the xp of that level; pays its reward. Unlocks the black market at level 5. |
| `complete_tutorial` | step | Marks the tutorial as completed. |
| `set_goals` | goal id, state JSON | Stores a goal's progress. |
| `complete_goal` | goal id | Pays a goal's reward, once per goal. |
| `complete_collection` | collection id | Pays a collection reward, once; needs every dragon of the collection. |
| `weekly_reward` | `"[reward, dragon]"` | The Monday bonus; once every 5 days. |
| `set_help_map` | help id | Remembers a help tip as seen. |
| `buy_treasure_new`, `buy_treasure_popup` | treasure id | Buys gold or food with gems. |
| `deus_cards_generate` | paid, super | Draws a card prize (paid with gems, or one free draw per day). |
| `deus_cards_claim` | – | Claims the pending card prize, once. |

### Training and tournaments

| Command | Arguments | What it does / needs |
|---|---|---|
| `start_training` | building, dragon uid, attack id, slot | Starts training (the dragon can learn that attack; the building is free). |
| `speed_training` | building | Pays gems for the time left and teaches the attack. |
| `finish_training` | building | Teaches the attack once the training time has passed. |
| `begin_tournament` | – | Starts a tournament. |
| `end_tournament` | won, kills JSON | Ends it (needs a started tournament); on a win pays its reward and 50 points. |
| `admin_speed_tournament` | – | Pays gems to skip the cooldown between tournaments. |
| `set_attack_team` | type, ids JSON | Sets a team of up to 6 of your own dragons. |

### PvP and neighbours

| Command | Arguments | What it does / needs |
|---|---|---|
| `attack_player` | opponent id | Starts a fight against a PvP opponent; returns their dragons. |
| `end_attack_f` | opponent id, position, win, kills JSON | Reports the fight (needs `attack_player`, 10 s–1 h earlier); a win pays 35 points and counts towards the league. |
| `assist_neighbor` | neighbour id, clicks JSON | Queues a help for a friend (neighbour). |
| `assist_receive` | item type | Collects the reward of one received help. |
| `clean_received_assists` | helper id | Removes a helper's entry. |

### Black market

| Command | Arguments | What it does / needs |
|---|---|---|
| `kompu_boxes_new_list` | – | Shuffles a new board of six dragons (3 gems). |
| `kompu_boxes_open_box` | – | Opens the next box (20 gems the first, then 10). |
| `kompu_boxes_claim_prize` | – | Puts the opened box's dragon in the warehouse and resets the board. |

### Connection

| Command | Arguments | What it does |
|---|---|---|
| `sync`, `ping` | – | Keep-alive; nothing changes. |

> The authoritative list is the `Command` enum in `src/enums.py`; the exact rules
> are in each command module.
