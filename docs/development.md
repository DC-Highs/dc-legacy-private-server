# Development

## Setup

Requirements: Python 3.9+ with [Poetry](https://python-poetry.org/), Node 22+, and Docker if you
want real PostgreSQL and MongoDB.

```bash
poetry install                      # server + dev dependencies
cd frontend && npm install          # web client
```

## Running locally

The simplest way is Docker (see [deployment.md](deployment.md)). To work on the code with hot
reload:

1. Start only the databases and publish their ports on your machine, for example:

   ```bash
   docker run -d --name dc-pg -e POSTGRES_USER=dragon -e POSTGRES_PASSWORD=dev \
     -e POSTGRES_DB=dragoncity -p 127.0.0.1:25432:5432 postgres:16-alpine
   docker run -d --name dc-mongo -p 127.0.0.1:27018:27017 mongo:7
   ```

2. Point the server at them and start it:

   ```bash
   export POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=25432 POSTGRES_PASSWORD=dev
   export MONGO_URL=mongodb://127.0.0.1:27018
   poetry run python -m dragon_city migrate
   poetry run python -m dragon_city create-admin --email dev@example.com --password 'dev-password-1'
   poetry run python -m dragon_city serve        # http://127.0.0.1:8080
   ```

3. In another terminal, start the web client with hot reload:

   ```bash
   cd frontend && npm run dev                    # http://localhost:5173
   ```

   Vite proxies `/api`, `/static`, `/flash`, `/assets`, `/deploy` and `/stream` to the server
   (set `VITE_BACKEND_URL` if it is not on `127.0.0.1:8080`).

> Some ports are reserved by Windows (a `bind ... forbidden` error): pick another one.

## Tests

```bash
poetry run pytest
```

The suite needs no services: accounts use in-memory SQLite and game saves use `mongomock`
(see `tests/conftest.py`). What is covered:

| File | Covers |
|---|---|
| `test_auth.py` | Sign-up, login, logout, validation, enumeration, hashing, rate limit. |
| `test_csrf.py` | Cross-site and `Origin: null` requests. |
| `test_admin.py` | Admin access control and every admin operation. |
| `test_game_security.py` | The client-injection attempts listed in [SECURITY.md](SECURITY.md), plus a normal play session. |
| `test_web.py` | Health check, serving the web client, security headers. |

Tests that exercise the game use the `player` fixture (a registered, logged-in client), the
`packet(client, ("cmd", [args]), ...)` helper, and `edit_save()` to set up a scenario directly
in the database.

The web client has no automated tests; it is type-checked and built with `npm run build`.

## Database migrations

When you change `src/dragon_city/db/models.py`:

```bash
# with PostgreSQL running and reachable through the POSTGRES_* variables
poetry run python - <<'EOF'
from alembic import command
from dragon_city.cli import _alembic_config
command.revision(_alembic_config(), message="describe the change", autogenerate=True)
EOF
```

Review the generated file in `src/dragon_city/migrations/versions/` (remove SQLite-only
variants, check defaults), then `poetry run python -m dragon_city migrate`. To confirm the models
and the migrations agree, run `alembic.command.check(_alembic_config())`: it must report "No new
upgrade operations detected".

## Adding a command

A command is a module in `src/dragon_city/commands/`:

1. Add the wire name to the `Command` enum in `enums.py`.
2. Create `commands/<name>.py`:

   ```python
   import logging

   from dragon_city.commands.base import CommandContext, command
   from dragon_city.commands.validation import reject
   from dragon_city.enums import Command

   logger = logging.getLogger(__name__)


   @command(Command.MY_COMMAND)
   def handle(ctx: CommandContext) -> None:
       iso_id = ctx.iso_arg(0)                       # validated: a positive integer, as text
       amount = ctx.int_arg(1, "amount", 1, 100)     # validated: an integer within a range
       item = ctx.map_item(iso_id)                   # rejects when the object is not on the map

       ctx.pay(gold=amount * 10)                     # rejects when the player cannot afford it
       ctx.info["xp"] += 5
       ctx.result = "ok"                             # optional: what the client gets back
   ```

   The module is found automatically; there is nothing to register by hand.

3. Follow the rules the security model depends on:
   - read **every** argument through the `ctx.*_arg` helpers (never `ctx.args[i]` directly,
     except to keep a value exactly as sent after validating it);
   - validate **before** changing anything, and charge with `ctx.pay`, never with `max(0, ...)`;
   - values that grant resources must come from the server's config or state, not from the
     client's arguments;
   - ids chosen by the client (`ctx.new_uid`) must be checked for collisions;
   - raise `reject("...")` for anything wrong: the command becomes a no-op and the reason is
     logged. Unexpected exceptions are rolled back too.
4. Write a test in `tests/test_game_security.py` (or a new file): the valid case, and each way a
   client could abuse it.

Rule helpers live in `game/`; put logic shared by several commands there (see `inventory.py`,
`dragonarium.py`, `training.py`, `combat.py`).

## Web client

`frontend/` is Vite + React + TypeScript + Tailwind + shadcn/ui.

- `src/lib/api.ts` is the fetch wrapper (`ApiError` carries the server's field errors);
  `src/lib/auth.tsx` the auth context.
- `src/pages/` has the pages, `src/components/game/` the Ruffle integration
  (`ruffle.ts` builds the load options and the URL rewrite rules).
- Components come from shadcn: add one with `npx shadcn@latest add <name>`; don't hand-write
  UI primitives. Forms use `Controller` with the `Field` component and a zod schema; text uses
  the `Typography` component and links the `Link` component.
- Ruffle itself is loaded by a `<script>` tag in `frontend/index.html` (from unpkg).

Build: `npm run build` (output in `frontend/dist`, which the server serves; the Docker image
builds it for you).

## Conventions

- Python code is typed where it helps readability, with short docstrings on non-obvious
  functions. Logs go through `logging`, in English, never `print`.
- Commit messages explain the *why*; keep commits focused.
- Never commit `.env`, game files or build output (see `.gitignore`).
