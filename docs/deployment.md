# Deployment

## What runs

`docker compose up` starts three containers:

| Service | Image | Role |
|---|---|---|
| `app` | built from the `Dockerfile` | The Flask server (gunicorn) and the web client. Published on `APP_PORT`. |
| `postgres` | `postgres:16-alpine` | Accounts and login sessions. |
| `mongo` | `mongo:7` | Each player's save, PvP opponents, queued assists. |

The databases are on a private compose network and **publish no ports**. Their data lives in the
named volumes `postgres-data` and `mongo-data`.

On start-up the `app` container:

1. waits for PostgreSQL and applies the migrations (`python -m dragon_city migrate`);
2. starts gunicorn;
3. creates the MongoDB indexes, imports the bundled PvP opponents if the database is empty,
   creates the bootstrap administrator from `ADMIN_EMAIL`/`ADMIN_PASSWORD` (if set), and
   removes expired sessions.

## On your own PC

1. Install Docker Desktop.
2. Put the game files in `flash/`, `assets/` and `domains/` (see [configuration.md](configuration.md)).
3. `cp .env.example .env` and fill in the passwords and the admin account.
4. `docker compose up -d --build`
5. Open <http://localhost:8080> (or your `APP_PORT`).

> 📸 **Screenshot needed:** the terminal after `docker compose up -d --build`, showing
> `docker compose ps` with the three services `healthy`.
> Save it as `docs/images/compose-ps.png`, then replace this block with
> `![The three services running](images/compose-ps.png)`.

Useful commands:

```bash
docker compose logs -f app          # follow the server log
docker compose ps                   # status and health
docker compose down                 # stop (data is kept in the volumes)
docker compose down -v              # stop AND delete all data
```

## On a VPS

Everything above applies, plus:

### 1. HTTPS

Passwords and the login cookie must not travel in clear text. Put a reverse proxy that
terminates HTTPS in front of the app (nginx, Traefik, Caddy, ...), forward it to
`127.0.0.1:<APP_PORT>`, and in `.env` set:

```
COOKIE_SECURE=true
TRUST_PROXY=true
```

`COOKIE_SECURE` makes the browser send the cookie only over HTTPS; `TRUST_PROXY` makes the app
use the real client address and scheme from the proxy headers (needed for rate limiting and
for the same-origin check).

If you want to publish only to the proxy, change the port mapping in `compose.yaml` to
`"127.0.0.1:${APP_PORT:-8080}:8080"`.

### 2. Proxy settings that matter

- **Do not buffer `/stream`.** It is a Server-Sent Events stream (the "Saved" hint). The app
  already sends `X-Accel-Buffering: no`; with other proxies disable response buffering for that
  path.
- **Pass the original `Host` and `Origin` headers.** State-changing requests are rejected when
  `Origin` does not match the host the browser used.
- Long-lived requests are normal: keep read timeouts above ~60 s for `/stream` (the server
  sends a keep-alive every 20 s).
- Request bodies are small (packets are capped at 256 KB), so no large upload limits are needed.

### 3. One process only

The app runs **one gunicorn worker** on purpose (`docker/gunicorn.conf.py`): the live-save
notifications, the per-player locks and the rate limiter live in process memory. Concurrency
comes from 128 threads; each open game tab holds one thread for its event stream. Do not run
several replicas behind a load balancer. If you ever need to scale, those three things must
first move to a shared store (for example Redis).

### 4. Firewall

Only the proxy's port (80/443) should be reachable from the internet. The `app` port and the
databases should not be exposed publicly.

## Registration and the first administrator

- Set `REGISTRATION_ENABLED=false` if only you should create accounts (admins can still create
  them from `/admin`).
- If you did not set `ADMIN_EMAIL`/`ADMIN_PASSWORD`, create an administrator:

  ```bash
  docker compose exec app python -m dragon_city create-admin --email you@example.com --password '...'
  ```

  `ADMIN_PASSWORD` stays in `.env`; change the password in the panel after the first login and
  consider clearing it from the file.

## Backups

Back up both databases; the saves alone are not enough, because accounts (and the ids that link
them to saves) live in PostgreSQL.

```bash
# PostgreSQL (accounts, sessions)
docker compose exec -T postgres pg_dump -U dragon dragoncity > accounts.sql

# MongoDB (saves, PvP opponents)
docker compose exec -T mongo mongodump -u dragon -p "$MONGO_PASSWORD" \
  --authenticationDatabase admin --db dragoncity --archive > saves.archive
```

Restore:

```bash
docker compose exec -T postgres psql -U dragon dragoncity < accounts.sql
docker compose exec -T mongo mongorestore -u dragon -p "$MONGO_PASSWORD" \
  --authenticationDatabase admin --archive --drop < saves.archive
```

If a player's save is missing but the account exists (for example after restoring only
PostgreSQL), a fresh save is created the next time they log in.

## Updating

```bash
git pull
docker compose up -d --build
```

The new container applies any new migrations before serving. The databases are untouched
because they live in volumes. Players with the game open will be disconnected for a few
seconds; their sessions stay valid.

## Troubleshooting

| Symptom | Check |
|---|---|
| `docker compose up` says `Set POSTGRES_PASSWORD in .env` | Create `.env` from `.env.example`. |
| `app` is `unhealthy` | `docker compose logs app`: usually a wrong database password or a database that is still starting. |
| The login works but you are logged out at once | `COOKIE_SECURE=true` over plain HTTP: the browser drops the cookie. Use HTTPS or set it to `false` locally. |
| Every request is `403 Cross-site request blocked` | The proxy changes the `Host` header, or the site is reached through another origin. Pass `Host` unchanged and set `TRUST_PROXY=true`; add the origin to `ALLOWED_ORIGINS` if needed. |
| The game area stays black / "Ruffle did not load" | The browser could not load Ruffle from `unpkg.com` (offline or blocked). |
| Missing sprites or sounds | The `assets/` volume is empty or mislabeled; the log shows 404s under `/assets/`. |
| `Rejected <command> from player ...` in the log | A command failed validation. One-off lines are normal; many from one player mean a modified client. See [SECURITY.md](SECURITY.md). |
