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
4. **Always verify** the PR was created by calling `mcp__github__pull_request_read` immediately after. Only tell the user the PR link once the MCP tool confirms it exists and is open.
5. **Before adding commits** to an existing PR branch, check if the PR is still open with `mcp__github__pull_request_read`. If it was already merged, create a new branch from `origin/main`, cherry-pick the pending commits, push, and open a new PR.

## Versioning

### Three versioning files — know which to touch

| File | Who sets it | Rule |
|------|-------------|------|
| `ha-addon/NEXT_VERSION` | **PRs** | Next version to release (plain `X.Y.Z`). The only version file PRs should edit. |
| `ha-addon/config.yaml` `version` | **Release workflow only** | Always the last *released* version. **Never edit in PRs.** The release workflow writes NEXT_VERSION here when cutting a release. |
| `ha-addon-dev/config.yaml` `version` | **PRs** | Tracks `{NEXT_VERSION}b{N}` (pre-release suffix). |

**Why keep `config.yaml` at the last released version?**
HA Supervisor reads `config.yaml` from the default branch. If it shows a version for which no Docker image exists yet, users see a broken "update available" prompt. Keeping `config.yaml` at the last released version prevents this. The release workflow atomically bumps it + publishes the image in one workflow run.

### Rule: what to do in every PR

1. **Read `ha-addon/NEXT_VERSION`** — all changelog entries go under `## [Unreleased]` for that version.
2. **Check if NEXT_VERSION is already released:**
   ```
   mcp__github__get_latest_release  owner=nsaputro  repo=siap-jalan
   ```
   - **If latest release tag < NEXT_VERSION** → NEXT_VERSION is still unreleased. Leave it as-is.
   - **If latest release tag == NEXT_VERSION** → bump NEXT_VERSION to the next semver and update `ha-addon/NEXT_VERSION`.
3. **Never touch `ha-addon/config.yaml` version in PRs.**
4. **Bump `ha-addon-dev/config.yaml`** as described below.

Use semantic versioning (`MAJOR.MINOR.PATCH`) when bumping NEXT_VERSION:
- `PATCH` (e.g. `0.1.3` → `0.1.4`) — bug fixes and small improvements
- `MINOR` (e.g. `0.1.x` → `0.2.0`) — new user-facing features
- `MAJOR` — breaking changes

### Pre-release version must always track NEXT_VERSION

`ha-addon-dev/config.yaml` must always be `{NEXT_VERSION}b{N}`:

1. Read `ha-addon/NEXT_VERSION` (e.g. `0.1.4`).
2. List existing pre-release tags:
   ```
   mcp__github__list_tags  owner=nsaputro  repo=siap-jalan
   ```
   Filter for tags like `v0.1.4b*`. Find the highest `b` number; `X = highest + 1`. If none exist, `X = 1`.
3. Set `ha-addon-dev/config.yaml` `version` to `{NEXT_VERSION}b{X}` (e.g. `0.1.4b1`).
4. **Every PR that adds new code must bump this value** — even when NEXT_VERSION itself did not change. The correct value is always strictly greater than every existing tag. If the current `ha-addon-dev/config.yaml` matches an existing tag, bump it.

**Example:** NEXT_VERSION=`0.1.4`, tags include `v0.1.4b2` → dev becomes `0.1.4b3`.
**Example:** NEXT_VERSION bumped from `0.1.4` → `0.1.5`, no `v0.1.5b*` tags → dev becomes `0.1.5b1`.
**Example:** NEXT_VERSION=`0.1.3`, current dev is `0.1.3b4`, tag `v0.1.3b4` already exists → dev becomes `0.1.3b5`.

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
- `packing_items` — list_id (FK), name, quantity, is_packed, is_essential, added_by (ai|user), source_activities (JSON)
- `trip_templates` — name, description, activities (JSON), climate_type, duration_range

### AI-powered suggestions

- `app/services/ai_suggestions.py` — generates packing list suggestions based on destination, trip type, duration, activities, and weather via Anthropic Claude API
- `app/services/weather.py` — fetches weather forecast for destination to inform packing suggestions
- Smart deduplication: AI suggestions merged with user's existing items; duplicates flagged, not re-added


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

1. Go to **Actions → Release → Run workflow** (no inputs needed).
2. The workflow automatically:
   - Reads `ha-addon/NEXT_VERSION`
   - Writes that version into `ha-addon/config.yaml` with a `[skip ci]` commit pushed to `main`
   - Creates and pushes the `vX.Y.Z` tag
   - Builds and pushes images to GHCR
   - Creates a GitHub release
3. After the workflow completes, update `CHANGELOG.md`:
   - Move `## [Unreleased]` entries to `## [x.y.z] - YYYY-MM-DD`
   - Update the `[Unreleased]` comparison link from `v{old}...HEAD` to `v{new}...HEAD`
4. Update `ha-addon/CHANGELOG.md` — replace with **only the new version's bullet points** followed by the full-changelog link:
   ```markdown
   ## x.y.z

   - Added/Fixed/Changed: …

   ---

   [Full changelog](https://github.com/nsaputro/siap-jalan/blob/main/CHANGELOG.md)
   ```
5. Bump `ha-addon/NEXT_VERSION` to the next planned version (e.g. `0.1.4`).

**To ship a pre-release:**

1. Ensure `ha-addon-dev/config.yaml` version is `{NEXT_VERSION}b{N}` (see versioning rules above).
2. Merge the PR to `main`.
3. Go to **Actions → Pre-release → Run workflow** (no inputs — version read from `ha-addon-dev/config.yaml`).
