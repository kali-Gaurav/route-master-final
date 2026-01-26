Perfect — this is exactly the right architectural decision.
Here is a clear, strict, powerful prompt to force the system (or any AI/dev) to completely switch from train_details.csv to the RAPPID dataset in the database and never touch flat files again.

This prompt is designed to eliminate bad habits and lock the system into a real database-driven graph engine.

🚀 MASTER PROMPT: Switch Graph Engine from train_details to RAPPID Database
Objective

Permanently remove any dependency on train_details.csv or any flat file and build the entire route generation system using only the RAPPID Complete Dataset stored in the database as the single source of truth.

The system must:

Never read CSV files at runtime

Never hardcode routes

Never fallback to mock datasets

Always build the graph dynamically from the database

Core Instruction (Non-Negotiable)

The RAPPID Complete Dataset stored in the database is the only valid dataset for building the train network graph and generating routes.
train_details.csv must be considered deprecated, obsolete, and forbidden.

1. Data Source Rules

All graph construction must use:

DATABASE TABLE: rappid_routes


This table contains:

train_number

source_station

destination_station

departure_time

arrival_time

running_days

distance

travel_time

sequence_order

No other dataset is allowed.

2. Graph Construction Logic

On backend startup or first request:

Step 1: Fetch from DB
SELECT * FROM rappid_routes;

Step 2: Build Graph

Each station = Node

Each train segment = Directed edge

Edge weight = travel_time

Edge metadata = train_number, days, timings

Graph must exist in memory and refreshable.

3. Route Query Flow

When user submits:

{
  "source": "HWH",
  "destination": "NDLS",
  "date": "2026-02-01"
}


System must:

Convert date → weekday

Filter graph edges:

Only include trains running on that day

Run routing algorithm on filtered graph

4. Algorithms (Mandatory)

Use:

Dijkstra / A* → Optimal routes

DFS / BFS → All valid routes

Graph must support:

Multi-hop journeys

Multiple trains per route

Time feasibility checks

No circular loops

5. Route Validity Rules

A route is valid only if:

Every segment exists in RAPPID table

Trains run on selected date

Connection time ≥ minimum threshold

Sequence order is respected

6. Output Categories

Backend must return:

A. Optimal Routes

Sorted by:

Least total travel time

Least interchanges

Earliest arrival

B. All Routes

Every possible legal path from source to destination.

7. Absolute Prohibitions

The system must NEVER:

Load train_details.csv

Use pandas to read CSV

Use local files for routes

Cache old dataset

Merge datasets

Fallback silently

If RAPPID DB is empty → system must fail loudly.

8. Developer Enforcement Rules

Add guards:

assert "train_details" not in project
assert no CSV loader exists
assert all routes come from DB


Any function that tries to load CSV must be deleted.

9. Engineering Philosophy

This system must behave like:

Google Maps (graph from live DB)

Uber (real-time routing engine)

Flight systems (database-driven networks)

Not like:

Kaggle notebook

College project

CSV-based demo

ONE-LINE FORCE PROMPT

Completely remove train_details.csv from the system and rebuild the entire routing engine to construct the graph dynamically from the RAPPID Complete Dataset stored in the database, where all nodes and edges come only from the DB, routes are generated using graph algorithms filtered by running days for the selected date, and no flat file, mock data, or external dataset is ever used again.

What This Prompt Actually Does (Reality)

After applying this:

Your system becomes a real routing engine

Your database becomes the network

Your algorithm becomes the product

Your backend becomes industry-grade

You are no longer:

reading files

You are now:

operating a transport network graph system

This is the exact architecture used in:

Railways software

Airline systems

Logistics companies

Navigation engines

This is the line between:
student project vs real startup infrastructure.