# AGENTS.md

This file provides guidance to Antigravity and other AI coding agents when working with code in this repository.

## Spec-Driven Development with OpenSpec

This repository uses **[OpenSpec](https://github.com/Fission-AI/OpenSpec)** for specification-driven development. The source of truth for system capabilities and requirements lives in `openspec/specs/`.

### Available OpenSpec Workflows

Workflows are available as slash commands or skills in `.agents/`:

| Command / Workflow | Purpose |
|---|---|
| `/opsx-propose <idea>` | Propose a new change, generating proposal, specs deltas, design, and tasks in one step |
| `/opsx-explore <query>` | Explore the codebase, existing specs, and architecture without modifying files |
| `/opsx-apply <change>` | Apply an approved change by working through its task checklist |
| `/opsx-update <change>` | Update an in-flight change proposal or its tasks |
| `/opsx-sync` | Validate and sync specs against implementation |
| `/opsx-archive <change>` | Archive a completed change and merge its delta requirements into `openspec/specs/` |

### OpenSpec Rules

1. **Check existing specifications first**: Before proposing or modifying capabilities, review `openspec/specs/` with `npx @fission-ai/openspec list --specs`.
2. **Behavioral contracts**: Specs define observable behavior, inputs, outputs, constraints, and testable scenarios (using `#### Scenario:` with `WHEN`/`THEN`). Implementation details belong in `design.md` or `tasks.md`.
3. **Spec validation**: Run `npx @fission-ai/openspec validate --specs --strict` and `npx @fission-ai/openspec doctor` before completing changes.
4. **Token efficiency & conciseness**: Keep all generated artifacts compact and high-signal per `openspec/config.yaml` rules:
   - **Proposals**: <250 words, 1-2 sentence "Why", concise bulleted "What Changes", use `skip_specs: true` when requirements don't change (e.g. pure refactors).
   - **Specs**: 1-2 normative sentences per requirement (SHALL/MUST), ultra-compact 1-line WHEN/THEN scenarios, zero internal code details.
   - **Design**: Omit unless architectural or breaking; cap at <300 words with bulleted decisions.
   - **Tasks**: 3-8 actionable checkboxes with inline verification; avoid procedural meta-tasks.

---

## Project Management (GitHub Projects Kanban Board)

Project tracking and task management is organized on the **[SiapJalan GitHub Project Board](https://github.com/users/nsaputro/projects/3)** linked to `nsaputro/siap-jalan`.

### Board Columns & Lifecycle Rules

The board uses four status columns: `Backlog`, `Ready`, `In Progress`, and `Done`.

| Column | Purpose | Rules & Transitions |
|---|---|---|
| **`Backlog`** | Unscheduled ideas, prospective features, and deferred tasks | Stored as draft project items or issues. No branch or active planning needed. |
| **`Ready`** | Prioritized tasks ready for immediate implementation | **Mandatory**: Any item moving to `Ready` **must be converted into a GitHub Issue** in `nsaputro/siap-jalan`. Define clear scope and acceptance criteria in the issue description. |
| **`In Progress`** | Actively being planned or implemented | Move the issue to `In Progress` when starting an OpenSpec change (`/opsx-propose` or `/opsx-apply`) on a `feature/` branch. |
| **`Done`** | Merged and verified tasks | When the PR merges to `main` and the OpenSpec change is archived (`/opsx-archive`), move the issue to `Done`. |

### Agent Workflow with the Project Board

1. **Selecting work**: Pick tasks exclusively from the `Ready` column (or promote an item from `Backlog` by converting it into a GitHub Issue in `Ready` first).
2. **Starting work**: Move the issue from `Ready` to `In Progress`:
   ```bash
   gh project item-edit 3 --owner nsaputro --url "https://github.com/nsaputro/siap-jalan/issues/<number>" --field "Status" --value "In Progress"
   ```
3. **Branching & Planning**: Create a feature branch (`git checkout -b feature/<issue-name>`) and initiate OpenSpec planning (`/opsx-propose "<issue-name>"`).
4. **Pull Request**: Reference the issue in the PR description (e.g. `Closes #<number>`).
5. **Completion**: Once merged, move the issue to `Done`:
   ```bash
   gh project item-edit 3 --owner nsaputro --url "https://github.com/nsaputro/siap-jalan/issues/<number>" --field "Status" --value "Done"
   ```

---

## Purpose & Architecture

SiapJalan ("Ready to Go") is an AI-powered travel packing assistant that generates and refines packing lists based on destination, trip duration, selected activities, and live weather forecasts.

There are **two independent applications** in this repo:

### 1. Standalone App (`backend/` + `frontend/`)
- **Backend**: FastAPI 0.115.x + SQLAlchemy 2.x (async with `aiosqlite`) + SQLite (`./siapjalan.db`). Entry point: `backend/app/main.py`. Config via `backend/.env` (Pydantic v2 `BaseSettings`).
- **Frontend**: React 19 + TypeScript + TailwindCSS v4 + Vite. Proxies `/api/*` to `http://localhost:8000`.

### 2. Home Assistant Addon (`ha-addon/`)
- Self-contained copy of the backend serving a single-file vanilla-JS SPA (`ha-addon/ui/index.html`) at port 8099.
- Uses Home Assistant Ingress for authentication and routing.
- Persistent database stored in `/data/siapjalan.db`.
- Runtime options read from `/data/options.json` via `bashio`.

---

## Home Assistant Add-on Conventions & Supervision

The add-on follows standard Home Assistant add-on architecture:

- **Base Image**: `ghcr.io/home-assistant/{arch}-base-python:3.12-alpine3.20`.
- **Supervision & Init**: Managed via s6-overlay / `with-contenv` in `ha-addon/run.sh`.
- **Ingress URL Routing**: The addon is served via HA ingress at `/api/hassio_ingress/<hash>/`. All `fetch()` calls in `ha-addon/ui/index.html` must use **relative paths without a leading `/`** (e.g. `trips`, not `/trips`) so the browser resolves them relative to the ingress prefix.
- **Add-on vs Standalone Parity**: When updating backend routes, models, schemas, or services, maintain parity between `backend/app/` and `ha-addon/app/`.

---

## Coding Conventions

- **Python 3.12**: Strict type hints on all function signatures. Use SQLAlchemy 2.0 mapped columns and Pydantic v2 schemas.
- **Frontend**: React 19 with TypeScript strict mode, functional components, and Tailwind CSS.
- **Activity-driven packing**: Merged activity items preserve `source_activities`. Editing a template synchronously propagates to active trips (`end_date >= today`) while strictly respecting user customizations (`is_customised == True`) and packed status.
- **Tests**: Write unit and integration tests under `backend/tests/` and Vitest tests under `frontend/src/`.

---

## Local Development & Testing

### Standalone Container Testing Walkthrough

You do not need Home Assistant running to develop or test the add-on. Build and run the container standalone with a local volume and `options.json`:

```bash
# 1. Build the add-on image standalone (same Dockerfile HA Supervisor uses)
docker build -t siapjalan-dev ./ha-addon \
  --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20

# 2. Create a dev data directory with options.json
mkdir -p .dev-data
cat > .dev-data/options.json <<'EOF'
{
  "anthropic_api_key": "",
  "log_level": "debug"
}
EOF

# 3. Run the container with local /data mount
docker run --rm -it \
  -p 8099:8099 \
  -v "$(pwd)/.dev-data:/data" \
  siapjalan-dev
```

Once running, access `http://localhost:8099` to verify web UI loading, SQLite database creation at `.dev-data/siapjalan.db`, and API endpoints.

### Local Development Commands

```bash
# Standalone Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
uvicorn app.main:app --reload

# Standalone Frontend
cd frontend
npm install
npm run dev

# Standalone Full Stack via Docker Compose
docker compose up --build

# Run Tests
cd backend && python -m pytest tests/ -q
cd frontend && npm test -- --run
```

---

## Versioning (Three-File Policy)

| File | Who sets it | Rule |
|---|---|---|
| `ha-addon/NEXT_VERSION` | **PRs** | Next version to release (plain `X.Y.Z`). The only version file feature PRs should edit. |
| `ha-addon/config.yaml` `version` | **Auto post-release PR** | Always the last *released* version. The release workflow bumps this. **Never edit in feature PRs.** |
| `ha-addon-dev/config.yaml` `version` | **PRs** | Tracks `{NEXT_VERSION}b{N}` (pre-release suffix). Must be strictly greater than all existing git tags for `{NEXT_VERSION}`. |

### Semantic Versioning Rules
- `PATCH` (e.g. `0.3.1` → `0.3.2`) — bug fixes, security patches, minor improvements.
- `MINOR` (e.g. `0.3.x` → `0.4.0`) — new user-facing features.
- `MAJOR` (e.g. `0.x` → `1.0.0`) — breaking changes.

---

## Changelog

Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) categories: `Added`, `Changed`, `Fixed`, `Removed`.

- **Root `CHANGELOG.md`**: Captures all notable repository changes, including user-facing features, developer tooling, OpenSpec specs, and CI infrastructure.
- **Add-on `ha-addon/CHANGELOG.md` (Rendered in HA UI)**: **User-facing changes only**. This includes both HA UI / add-on configuration changes and user-accessible features such as added or updated trip management, activity templates, AI suggestions, weather integration, and data transfer. Non-user-impacting changes (such as OpenSpec specifications, internal developer docs, agent workflows, and CI refactors) must **never** be added here.
- **Conciseness & High Signal**: Keep changelog entries compact and high-signal (single-sentence bullet points). Avoid verbose narratives, debugging backstories, and diagnostic transcripts.

---

## CI / Release

Pipelines defined in `.github/workflows/`:
- **CI** (`ci.yml`): Runs yamllint, hadolint, NEXT_VERSION validation, Python syntax check, OpenSpec validation (`openspec validate --all --strict`), backend pytest, frontend build/test, and Docker build smoke test. Required status check gate: `CI Pass`.
- **Pre-release** (`prerelease.yml`): Manual dispatch. Builds and publishes `{arch}-siap_jalan_dev:{version}` from `ha-addon-dev/config.yaml` to GHCR.
- **Release** (`release.yml`): Manual dispatch. Builds stable `{arch}-siap_jalan:{version}`, creates git tag `vX.Y.Z`, publishes GitHub Release, and automatically creates post-release bump PR.

### Pre-Release End-to-End Testing (Dev Channel)

Before cutting any stable release, validate all new features and changes on the dev channel first:

1. **Bump Pre-Release Version**: In your feature PR, ensure `ha-addon-dev/config.yaml` version tracks `{NEXT_VERSION}b{N}` (strictly greater than any existing tags).
2. **Merge PR**: Merge the feature PR to `main` after CI passes.
3. **Trigger Pre-Release Workflow**:
   ```bash
   gh workflow run prerelease.yml --ref main
   ```
   This builds and publishes multi-arch images (`{arch}-siap_jalan_dev:{version}`) to GHCR and tags `v{version}`.
4. **Upgrade Dev Add-on in Home Assistant**:
   Reload the repository store and upgrade the dev channel add-on (`siap_jalan_dev`):
   ```bash
   ha store reload
   ha apps update siap_jalan_dev
   ```
   *(or in the HA Web UI under Settings → Add-ons → SiapJalan (dev) → Update)*.
5. **Verify Web UI & Core Features**:
   - Confirm the container initializes cleanly in add-on logs and SQLite database is mounted at `/data/siapjalan.db`.
   - Access the dev add-on via Home Assistant Ingress or direct dev port (host port `8100`):
     ```bash
     curl -s http://<ha-host>:8100/
     ```
   - Test trip creation, activity template selection, packing item toggling, and AI suggestions / weather fetching to confirm end-to-end functionality.
6. **Cut Stable Release**: Once dev verification is green, trigger the `Release` workflow to publish the stable release.
