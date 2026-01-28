# Railway Operating System — Specification & Roadmap

Date: 2026-01-28

Purpose: transform the existing `railway-operating-system-core` into an "OS-like" command-driven system that can be run and automated on Windows (or any host) without a GUI. The system will expose a comprehensive set of commands to operate, query, analyze and report using only the bundled `production.db` and system files.

---

## Goals

- Provide a single CLI entrypoint and command registry (`rosctl`) that executes every operational task as a first-class system command.
- Support ad-hoc and scheduled operations (generate routes for a given origin/destination/date, nightly revenue runs, backups, data ingest).
- Maintain strong observability (structured logs, audit trail, job status) and safe operations (dry-run, idempotency where possible).
- Enable revenue and business-analysis workflows (fare simulation, demand forecasting, occupancy simulation, revenue aggregation).
- Make it easy to run as a Windows service or via Task Scheduler and support PowerShell automation.

---

## Core OS-like Features (High Level)

- Central CLI/dispatcher: `rosctl <command> [args]` with subcommands and help.
- Command registry & plugin system: commands register themselves, support for enabling/disabling modules.
- Job runner and scheduler: run-once jobs, cron/schedule jobs, retries, backoff, resource limits.
- Background worker: isolated process (or threadpool) to run CPU/IO heavy tasks, with job queue persisted (SQLite jobs table).
- Structured logging & auditing: JSON logs, per-command audit records stored in `logs/` and in DB table `system_audit`.
- Safe mode & dry-run: commands support `--dry-run` or `--simulate` to preview actions.
- Config & secrets: single `config.py` + env overrides; optional encrypted secrets store for credentials.
- Access control: local role-based permissions (admin/operators) enforced by a simple token or OS user mapping.
- Health & metrics: `/metrics` endpoint (Prometheus text or simple JSON) or a local metrics file.

---

## Route / Travel Features (what the OS executes on commands)

- `generate-routes`: produce all candidate routes between origin and destination for a specified date.
  - Parameters: `--source`, `--dest`, `--date`, `--max-transfers`, `--max-results`, `--sort-by`, `--format` (json/csv), `--cache`.
  - Outputs: writes to `data/routes/<source>_<dest>_<date>.json` (deterministic), prints a summary.
  - Options: `--background` (send to job queue), `--notify` (email/teams via hook), `--force` (ignore cache).

- `route-scan-batch`: run generate-routes for a list of O-D pairs (CSV) — handy for scheduled route scans.
- `route-validate`: run integrity checks on produced routes (running days, wait-times, day offsets).
- `route-export`: export route listings to CSV/Excel/PDF for downstream systems.

---

## Revenue & Business Analysis Features

- `revenue-simulate`: run fare scenarios across selected routes and dates.
  - Input: fare-mapping rules, occupancy profiles, frequency of runs.
  - Output: per-route and aggregated revenue projection CSV/JSON.

- `occupancy-forecast`: project occupancy per class across trains using historical utilization heuristics.
- `price-optimizer`: run simple search over price adjustments (discrete steps) to estimate incremental revenue.
- `revenue-report`: scheduled weekly/monthly rollup that computes realized revenue from `train_fares` and estimated occupancy.
- `what-if`: scenario engine to simulate route frequency/fleet changes and their revenue impacts.

---

## Data & Administration Tasks

- `ingest-dataset`: safe ingestion pipeline for new route/station/train data with validation and dry-run.
- `backup-db`: create timestamped copy of `production.db` to `backups/` and optionally upload to configured storage.
- `restore-db`: restore from backup with verification checks.
- `db-check`: run SQL integrity checks and surface missing indices or anomalies.
- `reindex`: rebuild critical indexes for search performance.
- `purge-cache`: remove temporary or cached route files older than N days.

---

## System & Observability

- `job-status`: list background jobs and their statuses (queued, running, success, failed).
- `job-log`: retrieve logs for a specific job id.
- `metrics`: local metrics snapshot (CPU, memory, DB queries, routes/sec) output in JSON.
- `profile-route`: run a profiling task on a heavy `generate-routes` run and save raw cProfile output.

---

## Windows Integration

- Provide PowerShell helper scripts (e.g., `rosctl.psm1`) to wrap common tasks and integrate with Task Scheduler.
- Provide a `Install-RosService.ps1` script that installs `rosctl` as a Windows service using `nssm` or `pywin32` (optional).
- Provide scheduled task examples to run `route-scan-batch` nightly and `revenue-report` weekly.

---

## Security and Safety

- Commands run in a sandboxed environment: heavy tasks run in worker process with resource constraints.
- Audit trail: every command invocation logged in `system_audit` with user (OS user or token), args, started_at, finished_at, status.
- Access tokens or OS user mapping to admin/operator roles for destructive commands (restore-db, ingest-dataset).

---

## Example Commands (usage)

- Generate routes now (foreground):

  python rosctl.py generate-routes --source NDLS --dest HWH --date 2026-01-28 --max-transfers 2 --format json

- Start a background job and get job id:

  python rosctl.py generate-routes --source NDLS --dest HWH --date 2026-01-28 --background

- Batch run routes from CSV:

  python rosctl.py route-scan-batch --input data/od_pairs.csv --date 2026-01-28 --concurrency 4

- Run hourly revenue summary (scheduled):

  python rosctl.py revenue-report --start-date 2026-01-01 --end-date 2026-01-31 --output reports/revenue_jan.json

- Backup DB (run as admin/operator):

  python rosctl.py backup-db --dest backups/ --compress

---

## Implementation Roadmap (Milestones)

1. Spec & command registry (this file + `rosctl.py`) — 1 day
   - Add a small command registry and help system using `argparse` or `click`.
2. `generate-routes` as a CLI wrapper — 1–2 days
   - Reuse `RouteFinder.find_all_routes`, wire `--date` to `start_date`, add caching and file output.
3. Job runner & simple scheduler — 2–3 days
   - Add `jobs` table, simple queue processor, `ros_worker.py` that picks queued jobs and runs them.
4. Batch/exports/reports (revenue & occupancy) — 3–5 days
   - Implement `revenue-simulate`, `revenue-report` and exporters.
5. Windows integration & PowerShell modules — 1–2 days
   - Add `Install-RosService.ps1` and `rosctl.psm1` convenience module.
6. Observability / auditing / profiling — 2 days
   - Add `system_audit`, structured logging, metrics snapshotting and profiling helper.
7. Tests & CI — ongoing (add tests while building features)

Estimated rough total: 2–3 weeks for a robust v1 that runs locally and under Windows scheduler; more time to harden, add RBAC, or scale worker fleet.

---

## Suggested New Files / Modules

- `rosctl.py` — CLI dispatcher and command registry
- `ros_worker.py` — background worker and runner
- `jobs.py` — job table helpers and job models
- `reports/revenue.py` — revenue simulation & reporting
- `scripts/Install-RosService.ps1` — Windows service helper
- `scripts/rosctl.psm1` — PowerShell helper module
- `data/routes/` — storage for generated route outputs
- `backups/` — DB backups
- `logs/` — structured logs and job logs

---

## Next Immediate Steps (I can implement these now)

1. Create `rosctl.py` CLI scaffold and wire `generate-routes` to `RouteFinder.find_all_routes` (fast win).
2. Add a `jobs` table and a simple `ros_worker.py` that can run queued `generate-routes` requests.
3. Add `backup-db` and `db-check` commands.

If you want, I can implement step 1 now: scaffold `rosctl.py`, add command parsing, and wire `generate-routes` with file output and `--background` flag (which will enqueue if `jobs` exists). Tell me to proceed and I'll start coding.

---

File created: `OPERATING_SYSTEM_SPEC.md`
