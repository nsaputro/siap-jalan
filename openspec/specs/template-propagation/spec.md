## Purpose

Propagates activity template modifications to active trips while preserving user customizations and packed state.

## Requirements

### Requirement: Synchronous Atomic Propagation to Active Trips
The system SHALL automatically propagate template modifications to all active trips where the trip end date is on or after the current date.

#### Scenario: Propagating new template item
- **WHEN** an item is added to an activity template
- **THEN** the new item is inserted into the packing lists of all active trips using that activity.

#### Scenario: Propagating template item removal
- **WHEN** an uncustomized item is removed from an activity template
- **THEN** matching uncustomized items are deleted from active trips using that template.

### Requirement: Customization and Packed State Preservation
The system SHALL preserve user modifications and packed statuses during template propagation.

#### Scenario: Skipping customized items on update or delete
- **WHEN** a template item is updated or deleted but an active trip item has customised set to true
- **THEN** the trip item is left unchanged.

#### Scenario: Preserving packed items
- **WHEN** a template change is propagated to an active trip item that has packed set to true
- **THEN** the packed status remains true regardless of template changes.
