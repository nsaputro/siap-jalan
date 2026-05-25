# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5] - 2026-05-25

### Removed
- `category` removed from the entire data model: API schemas (Create/Update/Response), activity merger, AI suggestion prompt and response, JSON seed templates, frontend TypeScript types, and HA addon UI
- `CATEGORIES` constant removed from `backend/app/schemas/packing.py` and `frontend/src/types/index.ts`

### Changed
- HA addon UI redesigned for simplicity: flat item list with no category grouping, circle checkboxes, and an inline "Type to add new item" field — no modal required to add items
- AI suggestions no longer include or request category information; items use a silent backend default
- `MergedItemResponse` and `MergedItem` dataclass no longer expose `category`; sorted by name only

## [0.1.4] - 2026-05-25

### Fixed
- All packing category names changed from Indonesian to English: Pakaian→Clothing, Toilet & Kebersihan→Toiletries & Hygiene, Dokumen→Documents, Elektronik→Electronics, Obat-obatan→Medications, Sepatu & Aksesoris→Shoes & Accessories, Makanan & Minuman→Food & Drinks, Olahraga→Sports & Fitness, Bayi & Anak→Baby & Kids, Lainnya→Other

## [0.1.3] - 2026-05-25

### Added
- `ha-addon/CHANGELOG.md`: per-addon changelog HA Supervisor reads to show "What's new" in the addon store

### Changed
- Pre-release version (`ha-addon-dev/config.yaml`) now tracks the upcoming stable version with a `bX` suffix (e.g. `0.1.3b1`) so testers always run a build that matches what will ship

### Fixed
- HA Supervisor no longer shows "No changelog found" when checking addon updates
- CLAUDE.md: added rule to always verify PR exists via MCP before announcing the link, and to check PR state before pushing additional commits
- CLAUDE.md: added rule to keep `ha-addon-dev/config.yaml` version in sync with the target stable version on every PR

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

[Unreleased]: https://github.com/nsaputro/siap-jalan/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/nsaputro/siap-jalan/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/nsaputro/siap-jalan/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/nsaputro/siap-jalan/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/nsaputro/siap-jalan/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/nsaputro/siap-jalan/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nsaputro/siap-jalan/releases/tag/v0.1.0
