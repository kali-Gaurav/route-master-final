# Tasks: Replace Static Route Data with Real-Time RAPPID Data

This file lists tasks (implementation + testing) to ensure that routes shown on the website are corrected using real-time train data from RAPPID (https://rappid.in/apis/train.php?train_no=XXXX). Tasks are grouped and prioritized. Aim: collect JSON per train, update route dataset, add validation, and exhaustive testing.

## Goals
- Replace static train metadata (train name, coach info, status, schedule where available) with live data from RAPPID.
- Store per-train JSON snapshots in `data/rappid/`.
- Provide a script to update CSV route files into `_updated.csv` and keep originals safe.
- Add API endpoints and UI enhancements to show live vs cached data and allow manual refresh.
- Create 50+ targeted tests to validate functionality and data integrity.

## Implementation Tasks
1. Create `scripts/update_routes_with_rappid.py` to scan `*_all_routes.csv` and fetch RAPPID for each unique train number.
2. Save raw RAPPID JSON responses to `data/rappid/<train_no>.json` (create folder if missing).
3. Produce updated CSV copies named `<orig>_updated.csv` where train name is replaced by live `train_name` (if present).
4. Add columns `rappid_last_updated` and `rappid_data_file` to the updated CSV.
5. Add optional flag `--overwrite` to replace original CSVs (default: false).
6. Implement concurrency with rate limiting (max N parallel requests, default 5).
7. Implement retry logic with exponential backoff (3 attempts) for RAPPID calls.
8. Add logging and a dry-run mode (`--dry-run`) to preview changes without writing files.
9. Add CLI args: `--csv-dir`, `--out-dir`, `--workers`, `--timeout`.
10. Add unit tests for the script (mock RAPPID responses) under `tests/test_update_routes.py`.

## Integration Tasks
11. Add a REST API endpoint `/admin/refresh-rappid/<train_no>` to refresh and store JSON for a specific train.
12. Add a bulk refresh endpoint `/admin/refresh-rappid-bulk` that accepts list of train numbers.
13. Add endpoint `/api/rappid-data/<train_no>` to serve stored JSON responses.
14. Update `/api/routes` to include `rappid_data` pointer when routes were updated from the RAPPID snapshot.
15. Add caching TTL configuration for stored JSON snapshots (default 24 hours) and a flag to force refresh.

## Data Validation & Cleaning Tasks
16. Validate `train_name` encoding and normalize whitespace/characters.
17. Extract and normalize station codes from RAPPID `data` entries (station_code/station_name mapping).
18. If RAPPID route contains platform info, map into CSV `platform` column where applicable.
19. Validate and store `coach_composition` if present.
20. Compute and store derived fields: `total_stations`, `first_station_code`, `last_station_code`.

## UI / Frontend Tasks
21. Add an admin page showing last refreshed times per train and a button to refresh.
22. Add badges next to route entries: `Live` (green) if updated within TTL, `Stale` (orange) otherwise.
23. Allow user to view raw RAPPID JSON for a train via an expandable panel for debugging.
24. Add toggle to prefer live RAPPID data for display vs original static dataset.

## Monitoring & Ops Tasks
25. Add telemetry: count of RAPPID calls, failures, average latency.
26. Add alerting for repeated RAPPID failures (3x consecutive errors for a train).
27. Create scheduled job to refresh high-priority trains daily (cron/Windows Scheduler).

## Security & Keys
28. Ensure any IRCTC RapidAPI keys are stored in environment variables (do not commit keys).
29. Add input validation on endpoints to prevent injection or path traversal when serving JSON files.

## Testing Tasks (50+ focused tests)
The following are precise tests to add across unit, integration, and E2E levels.

30. Unit: `rappid_client._make_request` retries on timeout and returns None after max attempts.
31. Unit: `rappid_client.get_train_data` uses cache when `use_cache=True`.
32. Unit: script dry-run mode returns expected changes without writing files.
33. Unit: CSV parser handles malformed rows gracefully (skips & logs warning).
34. Unit: `update_routes_with_rappid` respects `--workers` concurrency limit.
35. Unit: JSON files saved with proper UTF-8 encoding.
36. Unit: `train_name` normalization removes duplicate spaces and trims.
37. Unit: mapping function converts RAPPID station names to codes using `cities_locations.json` fallback.
38. Unit: generated `_updated.csv` contains `rappid_data_file` entries for every row.
39. Unit: retry/backoff logic triggers on HTTP 5xx and on connection errors.
40. Integration: `/api/rappid-data/<train_no>` returns stored JSON and correct 404 when missing.
41. Integration: `/admin/refresh-rappid/<train_no>` updates stored JSON and returns status.
42. Integration: `/api/seat-availability-by-train` returns route when stations missing.
43. Integration: `/api/seat-availability-by-train` calls IRCTC when stations provided.
44. Integration: Updated `/api/routes` includes `rappid_data` pointer when available.
45. Integration: Running `update_routes_with_rappid` twice does not duplicate files or corrupt CSV.
46. E2E: Frontend shows `Live` badge after refresh and clicking raw JSON opens content.
47. E2E: Database or storage layer maintains atomic writes for JSON files.
48. Performance: Bulk refresh of 500 trains completes within acceptable window (TBD based on infra).
49. Load: Concurrency test - 100 parallel `/api/rappid-data/<train_no>` requests without failures.
50. Regression: Route optimizer outputs unchanged when live data only updates train_name.
51. Regression: Route optimizer can accept coach_composition and reflect in UI if present.
52. Security: API endpoints validate train_no format and reject invalid inputs.
53. Data Quality: For every updated CSV, assert `train_name` non-empty for >95% of rows.
54. Data Completeness: Ensure per-train JSON includes either `data` array or a message field.
55. Edge Cases: Handle trains where RAPPID returns success=false gracefully and mark as 'no-data'.
56. Edge Cases: If RAPPID returns partial route, mark row as `partial_live_update` in CSV.
57. Unit: Script returns non-zero exit code on fatal errors and zero on success.
58. Integration: `run_deep_tests.py` includes test to confirm presence of `rappid_data_file` in routes response.
59. E2E: Nightly job to pick 100 high-traffic routes and assert their JSON is fresh (<24h).
60. E2E: Test for proper handling of rate limit responses (HTTP 429) from RAPPID.
61. Unit: Ensure JSON snapshots include `fetched_at` timestamp.
62. Integration: Health check includes count of stored RAPPID JSON files and last refresh time.
63. Load: Bulk CSV update for a single origin-destination runs without memory leaks.
64. Regression: Ensure dashboards that aggregate seat_prob continue to work with updated train names.
65. Integration: Endpoint `/admin/refresh-rappid-bulk` accepts CSV upload and returns manifest of updated trains.
66. Unit: Script logs are structured (JSONL) for ingestion by log aggregator.
67. E2E: Confirm that when IRCTC seat endpoint fails, `/api/seat-availability-by-train` returns helpful error and route data instead.
68. Security: Verify file permissions are set to prevent public write access to `data/rappid/`.
69. Documentation: Document how to run the update script, sample outputs, and rollback steps.
70. Cleanup: Add a script to delete `data/rappid/` JSONs older than N days.

## Next Steps
- I will add an automated script (`scripts/update_routes_with_rappid.py`) and a README snippet showing how to run it.
- After that I'll run the script against a small sample (e.g., the three trains you highlighted) and save data under `data/rappid/`.

---
Created: 2026-01-24
