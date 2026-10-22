# Configuration

The server is configured with environment variables. With Docker Compose you set them in a
`.env` file next to `compose.yaml` (start from `.env.example`); compose passes the right ones
to the containers. The code reads them in `src/config.py`.

## Compose variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | `8080` | Host port the game is published on. |
| `POSTGRES_PASSWORD` | – (required) | Password of the PostgreSQL `dragon` user. |
| `MONGO_PASSWORD` | – (required) | Password of the MongoDB `dragon` user. |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | empty | Bootstrap administrator, created at start-up if the email does not exist. Leave both empty to use the CLI instead. |
| `COOKIE_SECURE` | `false` | Send the login cookie only over HTTPS. **Set `true` behind HTTPS.** |
| `TRUST_PROXY` | `false` | Trust `X-Forwarded-For/Proto/Host` from one reverse proxy. Set `true` behind a proxy so rate limits see real client addresses. |
| `ALLOWED_ORIGINS` | empty | Extra origins allowed to send state-changing requests, comma separated. Normally empty: the web client and the API share one origin. |
| `REGISTRATION_ENABLED` | `true` | `false` stops public sign-ups; admins can still create accounts. |
| `SESSION_DAYS` | `14` | Days a login stays valid (renewed while in use). |
| `MAX_FRIENDS` | `20` | The most friends an account can have. Lowering it does not remove existing friends; it only blocks new ones. |
| `MAX_PENDING_REQUESTS` | `5` | Sent friend requests that can wait for an answer at once, per account. |
| `GAME_SWF` | `Base_sec_0.6.7c.swf` | The Flash client in `flash/versions/` loaded until an admin picks another one in the panel. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

Choose long random values for the passwords. They are only used inside the compose network.

## Application variables

These are set by `compose.yaml` and the `Dockerfile`; you only need them when running the
server without compose.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | built from `POSTGRES_*` | SQLAlchemy URL, e.g. `postgresql+psycopg://user:pass@host:5432/db`. |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `localhost`, `5432`, `dragon`, `dragon`, `dragoncity` | Used to build the URL when `DATABASE_URL` is empty (special characters in the password are escaped for you). |
| `MONGO_URL` | `mongodb://localhost:27017` | MongoDB connection string (without credentials). |
| `MONGO_USER`, `MONGO_PASSWORD` | empty | MongoDB credentials, authenticated against the `admin` database. |
| `MONGO_DB` | `dragoncity` | Database name. |
| `SEED_DIR` | `web/srv` (image: `/app/seed`) | Read-only seed data: game config, player template, PvP opponents. |
| `FLASH_DIR` | `flash` (image: `/data/flash`) | The Flash files: `DCLoader.swf` and the clients in `versions/`. |
| `ASSETS_DIR` | `assets` (image: `/data/assets`) | Game assets (sprites, sounds, fonts). |
| `DOMAIN_MAP_DIR` | `domains` (image: `/data/domains`) | Files that used to live on the game's original domains (translations, `crossdomain.xml`). |
| `FRONTEND_DIST` | `frontend/dist` (image: `/app/frontend/dist`) | The built web client. |

## Game files (volumes)

The Flash files and assets are large (hundreds of MB) and not ours to redistribute, so the
image does not contain them. `compose.yaml` mounts them read-only:

```yaml
volumes:
  - ./flash:/data/flash:ro
  - ./assets:/data/assets:ro
  - ./domains:/data/domains:ro
```

The small seed files in `web/srv/` *are* copied into the image:

| File | Purpose |
|---|---|
| `get_game_config.json` | The game's configuration (items, levels, goals, ...). May start with `<signature>;`; the loader accepts both forms. |
| `get_player_info.json` | Template for a new player's save. |
| `get_pvp_isle.json`, `pvp_players_info.json` | The initial PvP opponents; imported into MongoDB the first time the database is empty. |

## Constants in the code

| Where | What |
|---|---|
| `config.py` `SECRET_KEY` | The HMAC key the Flash client uses to verify signed packets. It ships inside the SWF, so it is not a secret. |
| `config.py` `PVP_PAGE_SIZE` | Opponents per league page (8). |
| `commands/collect.py` `GOLD_TOLERANCE` | Margin for the habitat gold check (see [SECURITY.md](SECURITY.md)). |
| `docker/gunicorn.conf.py` | One worker, 128 threads (see [architecture.md](architecture.md)). |
