## Purpose

Provides JSON export and import for trips, packing items, and custom activity templates across instances.

## Requirements

### Requirement: Comprehensive Data Export
The system SHALL export all active and future trips, packing lists, items, and custom activity templates as a single structured JSON payload.

#### Scenario: Exporting user data
- **WHEN** a user initiates an export request
- **THEN** a JSON document containing all trips, packing lists, items, and custom activity templates is generated.

### Requirement: Robust Data Import with Conflict Handling
The system SHALL import structured JSON data, restoring trips and custom templates while resolving slug conflicts.

#### Scenario: Importing data with existing templates
- **WHEN** an imported custom template slug conflicts with an existing template
- **THEN** the imported template is saved with a unique de-duplicated slug and associated items are restored.

#### Scenario: Importing partial or trimmed JSON
- **WHEN** an imported payload omits optional fields
- **THEN** sensible defaults are applied without failing validation.
