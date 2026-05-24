# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/nsaputro/siap-jalan/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/nsaputro/siap-jalan/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nsaputro/siap-jalan/releases/tag/v0.1.0
