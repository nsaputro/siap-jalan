## Purpose

Manages packing items, packed status toggling, ad-hoc entries, template promotion, and bulk item actions.

## Requirements

### Requirement: Packing Item CRUD and Status Toggle
The system SHALL support creating, updating, deleting, and toggling the packed status of individual items in a packing list.

#### Scenario: Toggling item packed status
- **WHEN** a client sends a toggle request for a packing item
- **THEN** the item packed state is inverted and the updated record is returned.

#### Scenario: Editing an item
- **WHEN** a user updates an item name, quantity, or essential flag
- **THEN** the updated attributes are saved and the item is marked as customised.

### Requirement: Ad-hoc Item Entry Under Activity Sections
The system SHALL allow users to add ad-hoc items to an existing trip associated with a specific activity grouping.

#### Scenario: Adding ad-hoc item to an activity section
- **WHEN** a user adds an item providing a source activity slug
- **THEN** the item is added to the trip list with added_by set to adhoc and template link set to null.

### Requirement: Promoting Ad-hoc Items to Activity Templates
The system SHALL allow promoting an ad-hoc packing item into the corresponding activity template for future trips.

#### Scenario: Promoting item to template
- **WHEN** a user requests promotion of an ad-hoc item
- **THEN** the item is added to the matching activity template and the packing item is linked to the new template item.

### Requirement: Bulk Item Operations
The system SHALL support bulk creation of packing items within a list.

#### Scenario: Bulk creating items
- **WHEN** a payload with multiple items is submitted to the bulk items endpoint
- **THEN** all items are validated and inserted into the specified packing list in a single transaction.
