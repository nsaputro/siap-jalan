## Purpose

Packages the application as a Home Assistant add-on with Ingress routing, options parsing, and data persistence.

## Requirements

### Requirement: Home Assistant Ingress Compatibility
The add-on SHALL serve a self-contained web user interface compatible with Home Assistant Ingress URL prefixes.

#### Scenario: Serving UI via Ingress
- **WHEN** a user accesses the add-on through the Home Assistant sidebar Ingress path
- **THEN** the single-page interface loads and routes API requests using relative paths without absolute root slashes.

### Requirement: Addon Configuration and Data Persistence
The add-on SHALL read runtime configuration from `/data/options.json` and persist all application data to `/data/siapjalan.db`.

#### Scenario: Starting add-on with options
- **WHEN** the add-on container initializes
- **THEN** configuration values such as log level and API keys are parsed from options and the SQLite database is created or migrated at `/data/siapjalan.db`.
