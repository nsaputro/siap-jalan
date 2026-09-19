## Purpose

Manages trip lifecycle records, destination metadata, packing list initialization, and progress tracking.

## Requirements

### Requirement: Trip Lifecycle CRUD
The system SHALL support creating, retrieving, updating, and deleting trip records with dates, destination, and activity selections.

#### Scenario: Creating a new trip
- **WHEN** a user submits trip details with destination, dates, and selected activity slugs
- **THEN** a new trip record is created and a default packing list is initialized.

#### Scenario: Deleting a trip
- **WHEN** a user requests deletion of an existing trip
- **THEN** the trip and all associated packing lists and items are permanently removed.

### Requirement: Automatic Packing List Pre-population
The system SHALL automatically populate a new trip's default packing list with merged items from selected activities upon trip creation.

#### Scenario: Trip creation with activities
- **WHEN** a trip is created with one or more activity slugs
- **THEN** the default packing list is seeded with deduplicated items from all selected activity templates.

### Requirement: Packing Progress Tracking
The system SHALL compute packing completion metrics for any trip based on packed vs total items.

#### Scenario: Computing packing percentage
- **WHEN** trip details or packing lists are retrieved
- **THEN** the response reflects the total item count, packed item count, and completion percentage.
