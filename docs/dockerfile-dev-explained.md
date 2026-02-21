# Understanding the Dev Dockerfile with `uv`

This document explains every line of the `Dockerfile.dev` written for a FastAPI project using `uv` as the package manager. It covers the reasoning behind each decision, common confusions, and why things are done the way they are.

---

## The Final Dockerfile

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8000

CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "app/main.py"]
```

---

## Line by Line Explanation

### `FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim`

This sets the **base image** — the starting point for your container. We're using an official image provided by the uv team that comes with both Python 3.12 and uv pre-installed.

> **Note:** The correct image is `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` (hosted on GitHub Container Registry). Using `astral/uv:...` will fail because that image doesn't exist on Docker Hub.

`bookworm-slim` refers to Debian Bookworm (a stable Debian release) in its minimal "slim" variant — meaning it's a lightweight base without unnecessary packages.

---

### `WORKDIR /app`

Sets the working directory inside the container to `/app`. All subsequent commands (`COPY`, `RUN`, etc.) will run relative to this path. If the directory doesn't exist, Docker creates it automatically.

---

### `ENV UV_LINK_MODE=copy`

This is an **environment variable** that uv reads automatically when it runs. You don't call it explicitly — uv picks it up in the background every time it installs packages.

#### Why is this needed?

When uv installs packages, it tries to **hardlink** files from its download cache into your project's virtualenv. Hardlinking is fast and saves disk space, but it only works when both locations are on the **same filesystem**.

Inside Docker, the cache (mounted temporarily during build) and the app directory (`/app`) are on **different filesystems**, so hardlinking fails. Setting `UV_LINK_MODE=copy` tells uv to just **copy the files instead**, which always works.

#### Why only one ENV here and not others?

The original Astral docs example includes three environment variables:

```dockerfile
ENV UV_COMPILE_BYTECODE=1   # compile .py to .pyc at install time (production optimization)
ENV UV_LINK_MODE=copy       # copy instead of hardlink
ENV UV_NO_DEV=1             # skip dev dependencies
```

For a **dev environment**, the other two don't make sense:

- `UV_COMPILE_BYTECODE=1` is a startup speed optimization for production. In dev, you're constantly changing code, so this adds unnecessary overhead at build time.
- `UV_NO_DEV=1` would skip installing dev dependencies like `pytest`, `ruff`, debuggers, etc. — exactly what you *need* in a dev container.

So only `UV_LINK_MODE=copy` is kept.

---

### The First `RUN` Installs Dependencies Only

```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
```

This is one `RUN` instruction with three parts: two `--mount` flags and the actual command. Let's break each one down.

#### `--mount=type=cache,target=/root/.cache/uv`

This mounts a **persistent build cache** at `/root/.cache/uv` inside the container during the build step.

uv stores all downloaded packages (wheels, source distributions) at this path. On your **first** `docker build`, uv downloads everything and fills this cache. On every subsequent build, uv finds the packages already cached and skips downloading them — making rebuilds much faster.

**Critical detail:** This cache is **never written into the final image**. It only exists on your host machine and gets temporarily mounted during the build. So your image stays lean, but your builds stay fast.

```
Build #1 → downloads fastapi, pydantic, uvicorn... (slow)
Build #2 → cache hit, skips all downloads (fast)
Build #3 → cache hit, skips all downloads (fast)
```

#### `--mount=type=bind,source=uv.lock,target=uv.lock`

This temporarily **binds** your local `uv.lock` file into the container at build time — without permanently copying it into the image.

Think of it as: *"make this file readable during this step only."*

`uv.lock` is uv's lockfile — it contains the exact pinned versions of every dependency your project needs.

#### `--mount=type=bind,source=pyproject.toml,target=pyproject.toml`

Same idea as above — temporarily binds `pyproject.toml` (your project manifest) into the container so uv can read what packages need to be installed.

#### Why use bind mounts instead of `COPY`?

This is about **Docker layer caching**. The goal is to separate dependency installation from your source code, so that changing your app code doesn't force Docker to reinstall all your packages.

If you had done `COPY pyproject.toml .` before this step, Docker would re-run the install every time `pyproject.toml` changes — even for unrelated changes. Bind mounts achieve the same result (uv can read the files) without creating a layer that gets invalidated.

#### `uv sync --locked --no-install-project`

- `--locked` — use the exact versions pinned in `uv.lock`. Don't resolve anything fresh.
- `--no-install-project` — install only the **third-party dependencies** (fastapi, pydantic, etc.), but skip installing your own project code. Your source code hasn't been copied into the image yet at this point, so this makes sense.

---

### `COPY . .`

Copies all your source code from your local machine into `/app` inside the container.

This happens **after** dependency installation intentionally. Docker caches each layer. If you change your app code and rebuild:

```
Layer 1: dependencies installed  ← CACHED (uv.lock didn't change)
Layer 2: COPY . .                ← re-runs (code changed)
Layer 3: project installed       ← re-runs
```

Without this separation, every code change would trigger a full dependency reinstall.

---

### The Second `RUN` Installs Your Project

```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
```

Now that your source code is in the image, this step installs **your actual project** on top of the already-installed dependencies.

This is why the `RUN` command appears twice — the first installs third-party packages, the second installs your own project. Splitting them maximizes Docker layer caching.

---

### `EXPOSE 8000`

Tells Docker that the container will listen on port 8000 at runtime. This is mainly **documentation** — it doesn't actually publish the port. You still need `-p 8000:8000` when running the container with `docker run`, or the `ports` mapping in `docker-compose.yml`.

---

### `CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0", "app/main.py"]`

This is the command that runs when the container starts.

#### Breaking it down

- `uv run` — activates the project's virtualenv and runs the following command inside it.
- `fastapi dev` — starts the FastAPI development server with hot-reloading enabled.
- `--host 0.0.0.0` — makes the server listen on **all network interfaces**, not just `localhost`. Without this, the server is only reachable from inside the container itself and your host machine can't connect to it.
- `app/main.py` — the entry point of your FastAPI application.

#### Why `--host 0.0.0.0`?

When you run `fastapi dev app/main.py` locally, the server binds to `localhost` (127.0.0.1) by default, which is fine — your browser is on the same machine.

Inside a container, `localhost` refers to the container itself, not your host machine. So you'd be unable to open `http://localhost:8000` in your browser. Adding `--host 0.0.0.0` makes the server accessible from outside the container.

#### Why `uv run` instead of just `fastapi`?

uv installs packages into a virtualenv at `/app/.venv/`. By default the container doesn't know to look there. `uv run` handles virtualenv activation automatically.

An alternative is to add the virtualenv to `PATH` explicitly:

```dockerfile
ENV PATH="/app/.venv/bin:$PATH"
CMD ["fastapi", "dev", "--host", "0.0.0.0", "app/main.py"]
```

Both approaches work. Using `uv run` is simpler and idiomatic for uv projects.

---

## Summary Table

| Line | What it does |
|---|---|
| `FROM ghcr.io/astral-sh/uv:...` | Start from official uv + Python base image |
| `WORKDIR /app` | Set working directory inside container |
| `ENV UV_LINK_MODE=copy` | Tell uv to copy files instead of hardlink (required in Docker) |
| First `RUN --mount ... uv sync --no-install-project` | Install third-party dependencies only, with build cache |
| `COPY . .` | Copy source code into the image |
| Second `RUN --mount ... uv sync` | Install your own project |
| `EXPOSE 8000` | Document that the app runs on port 8000 |
| `CMD ["uv", "run", "fastapi", "dev", ...]` | Start the FastAPI dev server on container startup |


## Docker Build

```sh
$ docker build -f Dockerfile.dev -t fast-api .
```

## Docker Run

```sh
$ docker run -p 8000:8000 -d --name fastapi fast-api:latest
```
