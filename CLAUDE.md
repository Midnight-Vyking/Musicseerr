# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

MusicSeerr is a self-hosted music request and discovery app built around Lidarr. Backend: Python/FastAPI. Frontend: SvelteKit 5/TypeScript. Packaged as a single Docker container.

## Commands

All common tasks are driven by `make`. Run `make help` to see all targets.

### Backend
```bash
make backend-venv          # Create Python venv
make backend-lint          # Ruff linting
make backend-type-check    # Mypy
make backend-test          # Full pytest suite
make backend-test-<name>   # Run a specific test category (e.g. make backend-test-lidarr)
```

Run backend locally: `cd backend && uvicorn main:app --reload --port 8688`

### Frontend
```bash
make frontend-install      # pnpm install
make frontend-build        # Production build
make frontend-test         # Vitest + Playwright
make frontend-type-check   # tsc
```

Run frontend locally: `cd frontend && pnpm run dev`

### Full CI pipeline
```bash
make ci                    # lint + format-check + type-check + tests (both sides)
make lint                  # backend + frontend linting
make format                # auto-format with Ruff + Prettier
```

### Docker
```bash
docker compose -f docker-compose.dev.yml up    # dev build from source
docker build .                                  # production image
```

## Architecture

### Backend (`/backend`)

**Entry point**: `main.py` — FastAPI app with lifespan context manager for startup/shutdown.

**Layered structure**:
- `api/v1/routes/` — thin route handlers; one file per domain (albums, artists, search, library, discover, requests, settings, playback sources, etc.)
- `services/` — business logic; composed from repositories
- `repositories/` — external service adapters (MusicBrainz, Lidarr, Jellyfin, Plex, Navidrome, Last.fm, ListenBrainz, YouTube, etc.)
- `infrastructure/` — cross-cutting: HTTP connection pooling, in-memory/disk cache, SQLite persistence, circuit breakers, retry logic
- `core/` — FastAPI dependencies (`core/dependencies/`), Pydantic settings (`core/config.py`), background task scheduling (`core/tasks.py`)
- `models/` — Pydantic input/output schemas; msgspec is used for high-performance JSON serialization in hot paths

**Persistence**:
- Config: `/app/config/config.json`
- SQLite DBs: `/app/cache/library.db`, `/app/cache/queue.db`
- Disk cache: `/app/cache/` (500 MB default, configurable TTL)

**Background tasks** (`core/tasks.py`): cache cleanup, library sync, discovery caching — scheduled at startup via the lifespan handler.

### Frontend (`/frontend/src`)

**Framework**: SvelteKit 5 with Svelte 5 runes syntax.

**Key directories**:
- `routes/` — file-based routing; pages for album, artist, discover, genre, library, playlists, profile, requests, search, popular, your-top
- `lib/api/` — TypeScript API client (typed wrappers around fetch)
- `lib/queries/` — TanStack SvelteQuery query/mutation definitions (server state)
- `lib/stores/` — Runed reactive stores with IndexedDB persistence (client state)
- `lib/player/` — Playback engine implementations: Jellyfin, Navidrome, Plex, Local, YouTube
- `lib/components/` — reusable UI components

**State management**: TanStack SvelteQuery for all server state (caching, background sync). Runed + IndexedDB for user preferences and persistent client state.

### Playback Sources

Multiple playback backends are first-class: Jellyfin, Navidrome, Plex, local file library, YouTube. Each has its own route file in `api/v1/routes/`, service in `services/`, repository in `repositories/`, and player implementation in `frontend/src/lib/player/`.

### External Integrations

| Purpose | Services |
|---|---|
| Download management | Lidarr (required) |
| Music metadata | MusicBrainz, TheAudioDB, Cover Art Archive, Wikidata |
| Playback | Jellyfin, Navidrome, Plex, local files, YouTube |
| Scrobbling | Last.fm, ListenBrainz |
| Discovery | ListenBrainz charts, Last.fm recommendations |

## Key conventions

- Python targets 3.13; use `async`/`await` throughout the backend.
- Pydantic models for all API boundaries; msgspec `Struct` for performance-sensitive serialization.
- Frontend uses Svelte 5 runes (`$state`, `$derived`, `$effect`) — not Svelte 4 stores syntax.
- All backend test categories map to a `make backend-test-<name>` target; add tests there rather than creating ad-hoc files.
- Config is managed through `core/config.py` (Pydantic `BaseSettings`); env vars and the JSON config file are both supported.
