## Purpose

Provides contextual AI packing suggestions and live destination weather forecasts to refine packing lists.

## Requirements

### Requirement: AI Packing Suggestions
The system SHALL generate destination-aware packing suggestions using destination, duration, activities, and weather context.

#### Scenario: Requesting suggestions with configured API key
- **WHEN** a user requests suggestions for a trip and the AI service is configured
- **THEN** a deduplicated list of recommended items is returned, excluding items already present in the trip list.

#### Scenario: Requesting suggestions without API key
- **WHEN** AI suggestions are requested but no API key is configured
- **THEN** a graceful error message is returned instructing the user to configure credentials.

### Requirement: Destination Weather Forecast Retrieval
The system SHALL fetch weather forecasts for trip destinations and dates from Open-Meteo.

#### Scenario: Retrieving weather forecast for trip dates
- **WHEN** a client requests weather forecast for a trip destination
- **THEN** forecasted temperatures, precipitation, and weather conditions are returned for the trip duration.
