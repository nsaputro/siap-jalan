## Purpose

Manages curated built-in and custom activity templates, template cloning, item visibility, and list merging.

## Requirements

### Requirement: Built-in Activity Templates Catalog
The system SHALL provide read-only built-in activity templates seeded with standard items for diverse travel activities.

#### Scenario: Listing built-in templates
- **WHEN** a client requests available activity templates
- **THEN** all built-in templates are returned with their names, icons, descriptions, and item catalogs.

### Requirement: Custom Activity Template Management
The system SHALL allow users to create, clone, update, and delete custom activity templates.

#### Scenario: Creating a custom template
- **WHEN** a user submits a new activity template with a name and icon
- **THEN** the template is created with a unique slug and stored as user-scoped.

#### Scenario: Cloning a built-in template
- **WHEN** a user requests cloning an existing template
- **THEN** a user-owned duplicate template is created containing all items from the source template.

### Requirement: Template Item Visibility and Modification
The system SHALL support adding, updating, hiding, and deleting items within custom activity templates.

#### Scenario: Toggling item visibility on cloned template
- **WHEN** a user toggles the visibility of an inherited template item
- **THEN** the item hidden flag is updated and excluded from subsequent trip packing list creations.

#### Scenario: Deleting user-added template item
- **WHEN** a user deletes an item created within a custom template
- **THEN** the item is removed from the template catalog.

### Requirement: Multi-Activity Template Merging
The system SHALL merge multiple selected activity templates into a single deduplicated item list.

#### Scenario: Merging overlapping activities
- **WHEN** a user requests merging templates with overlapping items
- **THEN** duplicate item names are resolved by taking the highest priority and maximum quantity, tagging all source activity slugs.
