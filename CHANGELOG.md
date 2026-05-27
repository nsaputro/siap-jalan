# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — next: 0.2.2

## [0.2.1] - 2026-05-27

### Added
- Two new built-in activity templates: **Essentials** (👕) with 14 clothing and personal items (t-shirts, underwear, socks, trousers, wallet, phone, medication, etc.) and **Toiletries** (🧴) with 15 hygiene items (toothbrush, toothpaste, shampoo, soap, deodorant, face wash, etc.); both appear at the top of the template list as universal trip additions
- Essentials and Toiletries are pre-selected by default when creating a new trip (both HA addon and React frontend)

### Fixed
- Built-in activity templates: replaced locale-specific abbreviations with generic English equivalents — "Passport / KTP" → "Passport / ID Card" (Flight template), "Car registration / STNK" → "Car registration documents" (Road Trip template)
- Template item editor: essential star (★) now turns gold/amber when toggled on, making the state visually distinct; also replaced `classList.toggle(force)` with explicit `add`/`remove` for cross-browser reliability (Safari)

## [0.2.0] - 2026-05-26

### Added
- Custom activity templates: users can create new activity templates from scratch, clone any built-in template to personalise it, and edit or delete their own templates — customisations are isolated by `ha_user_id` and propagate to all active and future trips
- `POST /activities/{slug}/clone` endpoint — creates a user-scoped copy of any template with all its items; slug is auto-generated and de-duplicated from the new name
- `ActivityTemplateCreate.slug` is now optional — auto-generated from the activity name when omitted
- HA addon UI: **Activities** tab with Clone (built-ins) and Edit / Delete (custom templates); inline template editor with auto-save, item management, and essential toggle; **+ New Activity** header button when the Activities tab is active
- React frontend: `/templates` page (built-ins with Clone, custom with Edit / Delete / New Activity) and `/templates/:id` edit page; **Activities** nav link on the Dashboard
- `ha-addon/CHANGELOG.md`: per-addon changelog HA Supervisor reads to show "What's new" in the addon store
- `ha-addon/NEXT_VERSION`: plain-text file holding the next unreleased version; PRs update this, never `config.yaml`
- **Item hide/show on personal templates**: built-in-derived items (cloned) cannot be deleted but can be hidden per user; hidden items are excluded from trip packing lists and the merge endpoint; user-added items (via the editor or inline add row) remain fully deletable; `is_hidden` and `is_user_added` flags added to `ActivityTemplateItem` with a startup migration for existing databases
- HA addon UI and React frontend template editor: visibility checkbox per item (checked = visible, unchecked = hidden); delete button shown only for user-added items; hidden items render dimmed
- HA addon UI trip detail: activity chips are now editable — tap ✕ to remove an activity (clears its auto-added items) or tap **+ Activity** to add a new one from an inline picker; changes propagate immediately to the packing list

### Removed
- `category` removed from the entire data model: API schemas (Create/Update/Response), activity merger, AI suggestion prompt and response, JSON seed templates, frontend TypeScript types, and HA addon UI
- `CATEGORIES` constant removed from `backend/app/schemas/packing.py` and `frontend/src/types/index.ts`

### Changed
- HA addon UI: packing list items now grouped by activity/template — each selected activity gets its own section header (emoji + name + packed count), with a "General" section at the bottom for untagged items; each section has its own inline "Add to …" row
- HA addon UI redesigned for simplicity: circle checkboxes, inline add rows per section — no modal required to add items
- AI suggestions no longer include or request category information; items use a silent backend default
- `MergedItemResponse` and `MergedItem` dataclass no longer expose `category`; sorted by name only
- Pre-release version (`ha-addon-dev/config.yaml`) tracks `NEXT_VERSION + bN` and is validated against `NEXT_VERSION` in the pre-release workflow
- Release workflow now writes version from `NEXT_VERSION` into `config.yaml`, commits to main, and tags — `config.yaml` on main always matches a published image

### Fixed
- Activity template mutating endpoints (`PUT`, `DELETE`, and item sub-endpoints) now enforce ownership: built-in templates return 403 on any mutation; custom templates return 403 if accessed by a different user
- All packing item category names updated to English
- HA Supervisor no longer shows "No changelog found" when checking addon updates
- CLAUDE.md: versioning rule updated — use `NEXT_VERSION` file; never bump `config.yaml` in PRs
- Dev addon 502 Bad Gateway: `ha-addon/run.sh` now uses `${PORT:-8099}`; `ha-addon/Dockerfile` accepts a `PORT` build arg; pre-release workflow passes `PORT=8100`
- HA addon UI trip card: activity badges now show the activity name and emoji instead of the internal slug code
- Trip card and trip detail: duration now calculated from dates when `duration_days` is not stored (e.g. trips created before the auto-calculate fix)
- Trip `duration_days` is now automatically calculated from `start_date`/`end_date` at creation time and recalculated when either date is updated (both backends)
- Updating a trip's activity list now correctly adds packing items for newly added activities and removes non-customised items that belonged exclusively to deselected activities (both backends)
- After removing or adding an activity from a trip, the packing list now reloads via a fresh GET to avoid stale ORM identity-map data showing items in the wrong section

## [0.1.2] - 2026-05-24

### Fixed
- HA addon UI now matches the Home Assistant theme in both light and dark mode.
  All hardcoded hex colors replaced with HA CSS custom properties
  (`--primary-color`, `--primary-background-color`, `--card-background-color`,
  `--primary-text-color`, `--secondary-text-color`, `--divider-color`,
  `--error-color`, `--secondary-background-color`).
  A `prefers-color-scheme: dark` media query provides dark-mode fallbacks when
  accessed outside HA. Form inputs, modals, badges, and progress bars all adapt.

## [0.1.1] - 2026-05-24

### Added
- `ha-addon-dev/` — dev/pre-release HA addon (slug: `siap_jalan_dev`, port: 8100, icon: `mdi:bag-suitcase-outline`) for testing new versions before stable release
- `ha-addon/config.yaml`: added `image:` field so HA pulls pre-built GHCR images instead of building locally
- `.github/workflows/prerelease.yml`: manual `workflow_dispatch` pipeline that validates the pre-release version suffix (e.g. `0.2.0b1`), creates a versioned git tag, builds and pushes `{arch}-siap_jalan_dev:{version}` to GHCR, and creates a GitHub pre-release
- Release workflow upgraded: matrix strategy for amd64/aarch64, auto-creates git tag on `workflow_dispatch`, appends install instructions to GitHub release notes

### Changed
- CI no longer publishes Docker images on `main` merge — image publishing is now exclusively owned by `release.yml` (stable) and `prerelease.yml` (pre-release)

### Fixed
- HA addon Dockerfile now uses addon-directory-relative COPY paths (`app/`, `ui/`, `data/`) so HA Supervisor can build the image locally without error. Previously the paths were repo-root-relative (`ha-addon/app/`, `data/`), which only worked in CI where the build context was the repo root.
- Added `ha-addon/data/activity_templates.json` so the seed data is inside the addon's build context.
- Updated CI and release workflows to set `context: ha-addon` for the HA addon Docker build steps to match the new Dockerfile paths.

## [0.1.0] - 2026-05-23

### Added
- Initial project boilerplate
- FastAPI backend with SQLAlchemy 2.x async ORM
- 6 data models: Trip, PackingList, PackingItem, ActivityTemplate, ActivityTemplateItem, UserTripTemplate
- 16 built-in activity templates (Flight, Beach, Hiking, Camping, Skiing, etc.)
- Activity merger service: combine multiple activities with smart deduplication
- Template propagation: editing an activity template updates all active trips
- Two item-add paths: template edit (propagated) vs ad-hoc to trip (one-off)
- AI packing suggestions via Anthropic Claude API
- Weather integration via Open-Meteo (free, no API key)
- Home Assistant addon: ingress support, multi-user via X-Ingress-User header
- Standalone Docker Compose deployment
- CI/CD: yamllint, hadolint, Python syntax check, Docker build test
- Release workflow: multi-arch Docker build + GitHub release
- Backend test suite: 60 tests (pytest + pytest-asyncio) covering trips, packing, activities, template propagation, activity merger
- Frontend test suite: 20 tests (Vitest + @testing-library/react) covering Zustand store, ActivityPicker, PackingProgress
- Backend-tests and frontend-tests CI jobs run on every PR
- `PackingItemBulkCreate` schema with `list_id` field for `/items/bulk` endpoint

[Unreleased]: https://github.com/nsaputro/siap-jalan/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/nsaputro/siap-jalan/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/nsaputro/siap-jalan/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/nsaputro/siap-jalan/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/nsaputro/siap-jalan/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nsaputro/siap-jalan/releases/tag/v0.1.0
