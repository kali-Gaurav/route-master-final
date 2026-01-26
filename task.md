🚀 Master Prompt: City-Based Station Autosuggestion & Route Engine

Objective:
Build a professional-grade travel search system where users can search by city name, get correct station autosuggestions, select source & destination, choose a date, and generate optimal + all possible train routes using a backend graph algorithm.

1. Frontend – Autosuggestion (City → Stations)

Implement a smart autosuggestion input field for both Source and Destination with the following behavior:

Input Behavior

As the user types (e.g. "Kolkata"), call:

GET /api/stations?q=kolkata


The backend returns all hub stations mapped to that city from city_hubs table.

If no city match is found, fallback to old station code/name search.

Dropdown UI

Show results in this format:

Kolkata (City)
  - Howrah Junction (HWH)
  - Sealdah (SDAH)
  - Kolkata Station (KOAA)

Selection Logic

When user clicks a station:

Store:

{
  label: "Howrah Junction",
  code: "HWH",
  city: "Kolkata"
}


Only the station code is sent to backend for route search.

2. UX Rules (Professional)

Show loading spinner while searching.

Debounce input (300ms).

Keyboard navigation (↑ ↓ Enter).

Cache last results.

Prevent free-text submit (must select from dropdown).

Highlight matched text.

Show city icon for city results, station icon for station rows.

3. Backend – Station Search Logic

/api/stations must:

First try:

SELECT * FROM city_hubs WHERE city ILIKE '%query%'


If found:

Return all mapped stations.

Else fallback:

SELECT * FROM stations WHERE name ILIKE '%query%' OR code ILIKE '%query%'

4. Route Search Flow

When user clicks Find Routes:

Frontend sends:

POST /api/routes
{
  "source": "HWH",
  "destination": "NDLS",
  "date": "2026-02-01"
}

5. Backend – Graph Algorithm

Build a graph:

Nodes = stations

Edges = train connections

Weights = travel time / distance / hops

Algorithm:

Use Dijkstra / A* for optimal routes.

Use DFS/BFS for all possible routes.

Filter:

Only trains that run on selected day of week.

Remove cancelled / inactive trains.

Respect minimum connection time.

6. Route Output Categories

Return two sections:

A. Optimal Routes (Top 3)

Sorted by:

Least travel time

Least interchanges

Highest reliability

B. All Valid Routes

Every possible legal path.

Each route must show:

Train numbers

Boarding station

Departure time

Arrival time

Intermediate stations

Total duration

Number of interchanges

7. UI – Route Display

Show as cards:

Optimal Routes (Highlighted)

Green badge: "Best"

Time graph

Visual station timeline

All Routes

Collapsible list

Filters:

Max interchanges

Night only

High-speed only

8. Edge Cases

System must handle:

Same city (multiple stations)

No direct route

Multi-day journey

Circular routes

Duplicate stations

Partial city name ("Kol" → Kolkata)

9. Data Source

Use the provided city-station mapping dataset as base:


cities_locations

This becomes your city_hubs master table.

10. Quality Bar (Must Match)

The final system should feel like:

Google Flights

IRCTC

Skyscanner

Rome2Rio

Not like a college demo.