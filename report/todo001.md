This is a very important design question, and thinking about it now will save you months of pain later.
What you want is not “just fetch data”, you want a living railway dataset.

The Core Problem You Identified (100% Correct)

Your current situation:

Train_details.csv

old

contains cancelled / legacy trains

missing new trains

static

But real world:

trains are added every month

some trains stop permanently

schedules change

platforms and routes change

So your dataset must become:

dynamic, self-updating, and authoritative

Not a one-time file.

The Right Concept: "Living Dataset"

Think of your system like this:

Internet (RAPPID / IRCTC)
        ↓
Fetcher Engine
        ↓
Raw Live Store (JSON)
        ↓
Clean Structured Store (CSV/DB)
        ↓
Routing Engine


Your CSV should be a cache, not the truth.

Step 1 – Where to Get "Today’s Valid Trains"

This is the key idea:

You should only store trains that actually exist today.

You discover active trains by:

Method A (Best)

From IRCTC seat search logs:

whenever a user searches route

store only trains that return success

This builds a real-world active set.

Method B (Batch)

From your old CSV:

try RAPPID for each train

if API returns success: false
→ drop that train forever

This cleans historical garbage.

Step 2 – Raw Fetch Layer (Never Overwrite)

For every valid train:

Store raw API output:

raw_rappid/
   16320.json
   12951.json
   22691.json


Never modify these.

These are your ground truth snapshots.

Step 3 – Structured Layer (Your Working Dataset)

From raw JSON, generate:

rappid_structured.csv


Columns like:

Column
train_no
train_name
station_seq
station_code
station_name
distance_km
arrival
departure
platform
halt
updated_time

This is what your algorithms use.

Step 4 – Smart Refresh Strategy

Never refetch everything.

Use this policy:

Case	Action
New train appears	fetch once
Train fetched < 7 days ago	use cache
Train fetched > 30 days ago	refresh
API says not found	deactivate

This makes your system:

fast

cheap

always current

Step 5 – Active / Inactive Flags

Your dataset should contain:

train_status:
   ACTIVE
   INACTIVE
   UNKNOWN


If RAPPID returns:

Response	Status
success true	ACTIVE
success false	INACTIVE
timeout	UNKNOWN

Never delete immediately — mark status.

This allows historical analysis.

Step 6 – How Routing Uses It

Routing engine must:

only use trains where status == ACTIVE


Everything else is ignored.

So even if CSV has 50,000 rows:
→ routing graph sees only real trains.

Step 7 – Storage Strategy (Do Not Stay on CSV Forever)

For small scale:

CSV + JSON


For real scale:

PostgreSQL or SQLite


Schema:

trains
stations
train_stations
fetch_logs


This allows:

fast queries

incremental updates

versioning

The Fetching Algorithm (Clear & Practical)

Here is the logic in plain English:

Start with empty active_trains set.

For each train number:

call RAPPID

if success:

save raw JSON

update structured table

mark ACTIVE

else:

mark INACTIVE

Repeat weekly for:

UNKNOWN trains

old ACTIVE trains

Why This Is Much Better Than "Download All"

Your current idea:

fetch all 11,000 trains every time

Correct system:

maintain 3,000–4,000 active trains forever

Brute force	Living dataset
hours	seconds
outdated	always current
static	self-updating
fragile	reliable
research-grade	production-grade
This Is Exactly How Real Companies Work

Google Transit:

never trusts static GTFS

continuously reconciles with live feeds

Uber:

never rebuilds city graph

only updates changed segments

Airlines:

never store full schedules forever

only keep active legs

Your Final Design in One Paragraph (Use This in Reports)

The system maintains a living railway dataset by continuously discovering active trains through live operational APIs, storing raw responses as immutable ground truth, and generating a structured working dataset that is incrementally refreshed based on time-to-live policies. Static historical files are treated only as bootstrap sources, while all routing decisions rely exclusively on trains marked ACTIVE through recent live validation.

That paragraph alone makes your project sound like real infrastructure engineering.

The Most Important Mindset Shift

Stop thinking:

"I need to download a dataset"

Start thinking:

"I need to operate a data pipeline"

You are no longer building a file.
You are building a system that keeps itself correct over time.

That’s the difference between:

a script

and a platform.