# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow — Before Implementing Any Feature

Follow these steps in order every time a feature or bug fix is requested:

1. **Read `PROJECT_PLAN.md`** to locate the feature in the milestone list and understand its scope and design intent.
2. **Read the relevant source files** before writing or modifying any code — routers, models, schemas, services, components, and tests that the feature touches. Never assume file contents from memory.
3. **Implement** the feature across both the standalone app (`backend/` + `frontend/`) and the HA addon (`ha-addon/`) where applicable, keeping the two in sync.
4. **Run tests locally** to confirm nothing is broken:
   ```bash
   cd backend && python -m pytest tests/ -q
   cd frontend && npm test -- --run
   ```
5. **Tick the item in `PROJECT_PLAN.md`** by changing `- [ ]` to `- [x]` for every checklist item the PR delivers. If all items in a phase are now checked, note that the phase is complete.
6. **Update `CHANGELOG.md`** under `## [Unreleased]` with what was added/changed/fixed.

## Git Policy

**Never push directly to `main`.** All changes must go through a pull request:

1. **Always** create the branch from the latest `main`: `git checkout origin/main -b feature/your-description`
2. Commit changes and push the branch
3. Open a PR targeting `main` via the GitHub MCP tools (`mcp__github__create_pull_request`)

## Versioning

**Before setting a version in any PR, always check the latest GitHub release first:**

```
mcp__github__get_latest_release  owner=nsaputro  repo=siap-jalan
```

The next version must be higher than the latest release. Never reuse an already-released version number. Use semantic versioning (`MAJOR.MINOR.PATCH`):

- `PATCH` bump (e.g. `0.1.2` → `0.1.3`) for bug fixes and small improvements
- `MINOR` bump (e.g. `0.1.x` → `0.2.0`) for new features
- `MAJOR` bump for breaking changes

Update `ha-addon/config.yaml` `version` field in the same PR as the change.

## Changelog

**Every PR that changes addon behaviour must update `CHANGELOG.md`.**

- Add an entry under `## [Unreleased]` in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format
- Use the categories `Added`, `Changed`, `Fixed`, `Removed` as appropriate
- When a release is cut, move `[Unreleased]` entries to a new `## [x.y.z] - YYYY-MM-DD` heading and update the comparison links at the bottom

## Development Commands

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # configure settings
uvicorn app.main:app --reload # http://localhost:8000, docs at /docs
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
npm run build   # type-check + production bundle
npm run lint    # ESLint on src/
```

### Full stack via Docker Compose

```bash
cp backend/.env.example backend/.env
docker compose up --build
# frontend → http://localhost:5173   backend → http://localhost:8000
```

### Tests

```bash
# Backend – run from backend/
cd backend
pip install -r requirements-test.txt   # first time only
python -m pytest tests/ -q             # all 60 tests (integration + unit)
python -m pytest tests/unit/ -q        # unit tests only (no DB seeding)

# Frontend – run from frontend/
cd frontend
npm test              # vitest in watch mode
npm test -- --run     # single run (used in CI)
npm run coverage      # generate coverage report
```

### Lint (CI checks run these)

```bash
yamllint -c .yamllint.yml ha-addon/config.yaml ha-addon/build.yaml
python3 -c "import ast, pathlib; [ast.parse(f.read_text()) for f in pathlib.Path('ha-addon/app').rglob('*.py')]"
```

## Architecture

There are **two independent applications** in this repo:

### 1. Standalone app (`backend/` + `frontend/`)

- **Backend**: FastAPI 0.135.x + SQLAlchemy 2.x + SQLite. Entry point: `backend/app/main.py`. Config via `backend/.env` (Pydantic v2 `BaseSettings`). Single-user personal app, no auth required.
- **Frontend**: React 19 + TypeScript + TailwindCSS v4 + shadcn/ui + Recharts. Vite proxies `/api/*` → `http://localhost:8000` (stripping the `/api` prefix) so all API calls use `/api/...` in the browser.
- **API client**: `frontend/src/api/client.ts` — fetch/axios with `baseURL: '/api'`.

### 2. Home Assistant addon (`ha-addon/`)

Self-contained copy of the backend with an HA-specific config and a vanilla-JS SPA (no build step needed). Key differences from the standalone app:

| Concern       | Standalone                  | HA Addon                                              |
| ------------- | --------------------------- | ----------------------------------------------------- |
| Config        | `backend/.env` via Pydantic | `/data/options.json` via `bashio::config` + env vars  |
| Database      | `./siapjalan.db`            | `/data/siapjalan.db` (persists across updates)        |
| Port          | 8000                        | 8099                                                  |
| Frontend      | React (Vite build)          | `ha-addon/ui/index.html` — single vanilla-JS file     |

The Dockerfile copies `ha-addon/ui/` → `/app/static/` in the container. `main.py` serves `static/index.html` at `/` and catches all unmatched routes for SPA navigation. **API routes are registered before the catch-all.**

**Critical — HA ingress URL routing**: The addon is served via HA ingress at `/api/hassio_ingress/<hash>/`. All `fetch()` calls in `ui/index.html` must use **relative paths without a leading `/`** (e.g. `trips`, not `/trips`) so the browser resolves them relative to the ingress prefix.

### Data models (`*/app/models/`)

SQLAlchemy 2.x tables (identical in both apps):

- `trips` — destination, start_date, end_date, duration_days, trip_type, activities (JSON), weather_destination, notes
- `packing_lists` — trip_id (FK), name, description, is_template
- `packing_items` — list_id (FK), category, name, quantity, is_packed, is_essential, added_by (ai|user)
- `trip_templates` — name, description, activities (JSON), climate_type, duration_range

### AI-powered suggestions

- `app/services/ai_suggestions.py` — generates packing list suggestions based on destination, trip type, duration, activities, and weather via Anthropic Claude API
- `app/services/weather.py` — fetches weather forecast for destination to inform packing suggestions
- Smart deduplication: AI suggestions merged with user's existing items; duplicates flagged, not re-added

### Packing categories

Standard categories tracked across all trips:
`Pakaian`, `Toilet & Kebersihan`, `Dokumen`, `Elektronik`, `Obat-obatan`, `Sepatu & Aksesoris`, `Makanan & Minuman`, `Olahraga`, `Bayi & Anak`, `Lainnya`

## CI / Release

There are **three pipelines**. CI never publishes images — that is exclusively owned by the release and pre-release workflows.

**CI** (`.github/workflows/ci.yml`) — runs on every push to `main`, `claude/**`, `feature/**` and on PRs:

- yamllint on `ha-addon/config.yaml` + `ha-addon-dev/config.yaml` + build.yamls
- hadolint on `ha-addon/Dockerfile` + `backend/Dockerfile`
- Python `ast.parse` syntax check on `ha-addon/app/` and `backend/app/`
- Backend pytest suite
- Frontend lint + build + Vitest suite
- Docker build smoke test for HA addon (no push)
- Docker build smoke test for standalone backend (no push)

**Pre-release** (`.github/workflows/prerelease.yml`) — `workflow_dispatch` only. Use for dev/beta/RC versions:

1. Enter a version with a pre-release suffix (e.g. `0.2.0b1`, `0.2.0rc1`). Pure `X.Y.Z` is rejected.
2. Version must match `ha-addon-dev/config.yaml` `version` field.
3. Builds and pushes `{arch}-siap_jalan_dev:{version}` to GHCR for amd64 + aarch64 (**no** `:latest` tag).
4. Creates a GitHub pre-release with install instructions for the dev channel (port 8100).

**Release** (`.github/workflows/release.yml`) — `workflow_dispatch` (preferred) or tag push:

1. Validates that the version matches `ha-addon/config.yaml` `version` field.
2. Builds and pushes `{arch}-siap_jalan:{version}` + `:latest` to GHCR for amd64 + aarch64.
3. Creates a GitHub release with install instructions.

**To ship a stable release:**

1. Check latest release: `mcp__github__get_latest_release`
2. Bump `version` in `ha-addon/config.yaml` to next `X.Y.Z`
3. Move `## [Unreleased]` entries in `CHANGELOG.md` to `## [x.y.z] - YYYY-MM-DD` and update comparison links
4. Merge via PR to `main`
5. Go to **Actions → Release → Run workflow** → enter the version number

**To ship a pre-release:**

1. Bump `version` in `ha-addon-dev/config.yaml` to e.g. `0.2.0b1`
2. Update `CHANGELOG.md`
3. Merge via PR to `main`
4. Go to **Actions → Pre-release → Run workflow** → enter the same version
