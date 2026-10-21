# Administration

## The admin panel

Administrators see an **Admin** button in the header and manage users at `/admin`.

![Header with the Admin button](https://i.ibb.co/yBN653tj/screenshot-2.png)

### Users list

A table of every account: email and id, the player's name, status (Active / Disabled, Admin),
level, gold, gems and last login. The search box matches part of an email or an exact id; the
list is paged (15 per page).

![The users table](https://i.ibb.co/39Wx71d3/image.png)

### Creating a user

"New user" asks for an email, a password (8–128 characters) and whether the account is an
administrator. It also creates a fresh game save, exactly like a sign-up.

![The New user dialog](https://i.ibb.co/hJ6484t9/image.png)

### Managing a user

"Manage" opens a dialog for one account:

| Control | Effect |
|---|---|
| Active | Disables the account and logs the user out; enabling lets them log in again. |
| Administrator | Grants or removes admin rights. |
| New password | Sets a password and logs the user out everywhere. |
| Resources | Sets the player's gold, gems and food. |
| Reset game save | Replaces the save with a fresh one (all progress is lost). Asks for confirmation. |
| Delete user | Deletes the account, its sessions and its save. Asks for confirmation. |

You cannot disable, demote or delete your own account from the panel, so an administrator can
never lock the system out by mistake.

![The Manage dialog](https://i.ibb.co/FkvYbYBz/image.png)

## Command line

Run these inside the app container (`docker compose exec app ...`) or, without Docker, with
`poetry run dragon-city ...`.

| Command | Purpose |
|---|---|
| `python -m src create-admin --email E --password P` | Create an administrator (or return the existing account with that email). |
| `python -m src migrate` | Apply the PostgreSQL migrations (the container does this on start). |
| `python -m src seed` | Import the bundled PvP opponents if the database has none. |
| `python -m src serve` | Development server on `127.0.0.1:8080` (production uses gunicorn). |

## PvP opponents

The PvP league lists bundled opponents. To add more, call the admin API
(`POST /api/admin/pvp/generate`, see [api.md](api.md)): it adds 8 random opponents with random
names, levels and teams per call.

## Reading the log

`docker compose logs -f app`. Lines worth knowing:

| Line | Meaning |
|---|---|
| `Command <cmd> \| args=... \| number=N` | A command received. |
| `Rejected <cmd> from player <id>: <reason>` | Validation refused it; the save was not changed. |
| `Command <cmd> (number N) failed` (with a traceback) | An unexpected error; the command was rolled back. Please report it. |
| `Command <cmd> is not implemented, ...` | The client sent a command this server does not handle yet. |
| `Player <id> claimed X gold from habitat ... but at most Y was produced` | The habitat gold estimate clipped a collection. If this happens to honest players, raise `GOLD_TOLERANCE` in `commands/collect.py`. |

Set `LOG_LEVEL=DEBUG` for more detail.

## Common tasks

- **A player forgot their password:** open the user in the panel and set a new one.
- **Ban someone:** switch Active off; their sessions end immediately.
- **Give a player resources:** Manage → Resources.
- **Close sign-ups:** set `REGISTRATION_ENABLED=false` and restart the app; you can still create
  accounts from the panel.
- **A save looks corrupted:** Reset game save restores a fresh one; to recover the old one,
  restore the MongoDB backup (see [deployment.md](deployment.md)).
