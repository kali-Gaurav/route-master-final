MASTER PROMPT: PRODUCTION DATA + BACKEND PIPELINE

You are a senior backend and data infrastructure engineer.
I am building a production-grade railway route discovery platform.
The system must generate valid routes from origin → destination → date using live operational data.

I do NOT want feature expansion.
I only want a robust, scalable, self-healing pipeline for:

data ingestion

data storage

business logic

API serving

system monitoring

Design and implement a complete advanced development-ready pipeline with the following strict requirements:

SYSTEM GOAL

Build a continuously running platform that:

Ingests live railway data from external APIs (RAPPID / IRCTC)

Stores immutable raw data snapshots

Derives clean, validated operational datasets

Serves route generation through APIs

Logs and analyzes system behavior over time

ARCHITECTURE REQUIREMENTS

The system must be split into these layers:

Ingestion Layer

Raw Data Store

Clean Operational Database

Business Logic Layer (Routing Engine)

API Layer (FastAPI)

Observability Layer (Metrics & Logs)

Each layer must be:

isolated

testable

replaceable

No layer should directly depend on CSV files.

DATA PIPELINE REQUIREMENTS
Ingestion Layer

async fetchers

rate limiting

retry logic

caching

background jobs (cron)

Raw Store

immutable

append-only

store full API payloads

never overwritten

Clean Store

normalized tables

validated schema

deduplicated

indexed for performance

DATABASE

Use:

SQLite for local

PostgreSQL compatible schema

Design full schema including:

trains

stations

train_stations

raw_payloads

search_logs

performance_logs

error_logs

Include:

primary keys

foreign keys

indexes

migrations strategy

BUSINESS LOGIC RULES

The routing engine must:

only read from clean database

never call external APIs directly

be deterministic

be testable in isolation

API LAYER

Expose:

POST /search
GET /routes
GET /metrics
GET /health

Must include:

input validation

idempotency

versioning

error handling

OBSERVABILITY

Track and store:

every user search

latency

API failures

cache hit rate

route success rate

background job status

Provide:

internal metrics API

JSON reports

AUTOMATION

Design background jobs:

refresh active trains daily

retry failed ingestions

clean expired cache

aggregate metrics hourly

NON-FUNCTIONAL REQUIREMENTS

The system must be:

reproducible

restart safe

crash resilient

horizontally scalable

free-stack compatible

No paid services.

DELIVERABLES

Generate:

Folder structure

Database schema

Core Python modules

FastAPI app

Background job runner

Logging system

Metrics system

Deployment guide

With:

clean separation of concerns

production coding style

extensive comments

DESIGN PHILOSOPHY

This is not a demo.
This is a long-running infrastructure system.

Focus on:

durability

observability

correctness

automation

Not on:

UI features

payment

ML models

authentication

Think like an engineer building:

Google Maps backend

Uber routing engine

Flight scheduling system

Produce a complete production-grade blueprint and implementation.