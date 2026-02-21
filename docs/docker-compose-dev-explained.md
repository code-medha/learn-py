# Understanding the Dev Docker Compose with `uv`

This document explains every line of the `docker-compose.dev.yml` written for a FastAPI project using `uv`. It covers the reasoning behind each decision, common confusions, and why things are done the way they are.

---

## The Final docker-compose.dev.yml

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    develop:
      watch:
        - action: sync
          path: .
          target: /app
          ignore:
            - .venv/
        - action: rebuild
          path: ./uv.lock

  post:
    image: postgres:13-alpine
    restart: always
    environment:
      - POSTGRES_DB=cruddur
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - '5436:5432'
    volumes:
      - post:/var/lib/postgresql/data

volumes:
  post:
    driver: local
```

---

## Line by Line Explanation

### `services`

Defines all the containers that make up your application. In this case two services: `app` (your FastAPI server) and `post` (PostgreSQL database).

---

### `app` service

#### `build`

```yaml
build:
  context: .
  dockerfile: Dockerfile.dev
```

- `context: .` — tells Docker to use the current directory as the build context (all files Docker can access during build)
- `dockerfile: Dockerfile.dev` — specifies which Dockerfile to use. Since this is a dev setup, we use `Dockerfile.dev` instead of the default `Dockerfile`

#### `ports`

```yaml
ports:
  - "8000:8000"
```

Maps port `8000` on your host machine to port `8000` inside the container. Format is `host:container`. Without this, the FastAPI server running inside the container is unreachable from your browser.

---

### `develop.watch` — The Hot Reloading Setup

This is Docker Compose's built-in file watching feature. It watches your local files and automatically syncs or rebuilds the container when they change — so you don't have to manually restart the container every time you edit code.

There are two actions available: `sync` and `rebuild`.

---

#### `action: sync` — For Code Changes

```yaml
- action: sync
  path: .
  target: /app
  ignore:
    - .venv/
```

- `path: .` — watch the entire project root on your local machine
- `target: /app` — when files change, sync them to `/app` inside the container
- `ignore: .venv/` — do NOT sync your local `.venv` folder (explained in detail below)

When you edit a `.py` file, Docker detects the change and copies it directly into the running container. No rebuild, no restart — the FastAPI dev server picks it up instantly via its own hot-reload.

**Why `path: .` and not `path: ./app`?**

Using `path: ./app` only watches your `app/` folder. Changes to other files like configs or `pyproject.toml` won't be synced. Watching the entire project root (`.`) is safer and more complete.

---

#### Why `.venv/` is Ignored — Important

Your local `.venv` is built for **your host machine's platform** (macOS or Windows). The container runs **Linux**.

Many packages like `pydantic`, `uvicorn`, and `cryptography` contain compiled binary files that are platform-specific:
- macOS binaries: `.dylib` files
- Linux binaries: `.so` files

These are not interchangeable. If your local `.venv` gets synced into the container:

```
your macOS .venv → synced into Linux container
                 → container tries to run macOS binaries on Linux
                 → crashes or throws weird errors
```

The container already has its own correct Linux `.venv` built during `docker build`. Syncing your local one would overwrite it with a broken one. That's why `.venv/` is explicitly ignored.

---

#### `action: rebuild` — For Dependency Changes

```yaml
- action: rebuild
  path: ./uv.lock
```

When `uv.lock` changes, it means someone added or removed a package. A simple file sync isn't enough — Docker needs to rebuild the entire image to install the new dependencies.

This watches `uv.lock` and automatically triggers a full `docker compose build` when it changes.

Without this, your manual workflow would be:
```bash
# painful manual process
1. notice uv.lock changed
2. stop the container
3. docker compose build
4. docker compose up
```

With `develop.watch`:
```bash
# automatic
uv.lock changes → Docker rebuilds automatically
```

---

### `develop.watch` vs Volumes — Common Confusion

You'll see many tutorials using volume mounts for hot reloading:

```yaml
# volume approach
volumes:
  - ./app:/app
```

They look similar but work very differently.

**Volumes (bind mount)** permanently mirror your entire local folder into the container in real time. Every file change is immediately reflected — but so is your local `.venv`, file permissions, and platform differences. `.dockerignore` does NOT help here because volumes bypass the image entirely and mount at runtime.

**`develop.watch` with sync** selectively syncs only what you specify, respects the `ignore` list, and gives you the extra power of `action: rebuild` which volumes can't do at all.

| | Volumes | develop.watch |
|---|---|---|
| How it works | mirrors everything instantly | selectively syncs |
| Can ignore files | ❌ No | ✅ Yes |
| Can trigger rebuild | ❌ No | ✅ Yes |
| `.venv` platform problem | ❌ Yes, bleeds in | ✅ No, you ignore it |
| `.dockerignore` respected | ❌ No | ✅ Yes |

**When are volumes fine?**
- You're on Linux locally (same platform as container, `.venv` binaries are compatible)
- You have no local `.venv` at all
- Simple pure-Python project with no compiled packages

**When is `develop.watch` better?**
- You're on macOS or Windows
- Your packages have compiled binaries
- You're using uv (Astral's own docs recommend `develop.watch`)

The reason you see volumes everywhere in tutorials is that most are older, written before `develop.watch` existed, or use simple projects where the platform mismatch doesn't cause visible problems.

---

### `post` service — PostgreSQL

```yaml
post:
  image: postgres:13-alpine
  restart: always
  environment:
    - POSTGRES_DB=cruddur
    - POSTGRES_USER=postgres
    - POSTGRES_PASSWORD=password
  ports:
    - '5436:5432'
  volumes:
    - post:/var/lib/postgresql/data
```

- `image: postgres:13-alpine` — uses the official lightweight PostgreSQL 13 image
- `restart: always` — automatically restarts the database container if it crashes
- `environment` — sets up the database name, user, and password
- `ports: 5436:5432` — maps port 5436 on your host to 5432 (PostgreSQL's default port) inside the container. Using 5436 on the host avoids conflicts if you have a local PostgreSQL already running on 5432
- `volumes: post:/var/lib/postgresql/data` — persists the database data to a named volume so your data survives container restarts

---

### `volumes` — Named Volume for Database

```yaml
volumes:
  post:
    driver: local
```

Declares the named volume `post` used by the PostgreSQL service. `driver: local` means it's stored on your local machine managed by Docker. Without this, your database data would be lost every time the container stops.

---

## How `uv run` Works Inside the Container

There's no interactive shell in Docker to run `source .venv/bin/activate` manually. So you have two options:

**Option A — `uv run` (what the Dockerfile uses):**
```dockerfile
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "app/main.py"]
```
uv handles virtualenv activation internally before running the command.

**Option B — put the virtualenv on PATH:**
```dockerfile
ENV PATH="/app/.venv/bin:$PATH"
CMD ["fastapi", "dev", "--host", "0.0.0.0", "app/main.py"]
```

Both work the same way. The Dockerfile uses Option A which is simpler.

---

## Workflow Commands

### Starting the dev environment with hot reloading

```bash
docker compose -f docker-compose.dev.yml watch
```

This is the key difference from the old `up` command. `watch` activates the `develop.watch` configuration — without it, file syncing and auto-rebuild don't happen at all.

Note that `watch` runs in the **foreground** (no `-d` flag support) so you can see sync and rebuild logs in real time.

### Stopping the dev environment

```bash
docker compose -f docker-compose.dev.yml down -v
```

`-v` removes the named volumes as well. Omit `-v` if you want to keep your database data between sessions.

### Full dev workflow

```bash
# start everything with hot reloading
docker compose -f docker-compose.dev.yml watch

# edit your code → changes sync automatically into the container
# add a new package with uv → uv.lock changes → image rebuilds automatically

# stop everything (in another terminal)
docker compose -f docker-compose.dev.yml down -v
```

---

## Summary Table

| Line | What it does |
|---|---|
| `build: dockerfile: Dockerfile.dev` | Use the dev-specific Dockerfile |
| `ports: 8000:8000` | Expose FastAPI server to host machine |
| `action: sync, path: .` | Sync all code changes into container instantly |
| `ignore: .venv/` | Don't sync local virtualenv (wrong platform) |
| `action: rebuild, path: ./uv.lock` | Rebuild image when dependencies change |
| `postgres:13-alpine` | Lightweight PostgreSQL database |
| `ports: 5436:5432` | Avoid conflict with local PostgreSQL on 5432 |
| `volumes: post` | Persist database data across container restarts |
| `docker compose watch` | Start everything with hot reloading active |
