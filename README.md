# EveArb v2.10

This build advances the live v2.08 baseline with the next practical layer:
- version text normalized to v2.10
- cargo realism on opportunities
- user setting for total m3 available
- per-opportunity total m3 necessary + fits cargo
- profit realism pass with broker fee + sales tax + hauling cost assumptions
- route security filter options aligned with backend

## Core behavior
- `Total m3 Available` is a per-user dashboard setting.
- The dashboard uses that value as the default cargo-cap filter when loading opportunities.
- Each opportunity now returns:
  - `total_m3_necessary`
  - `total_m3_available`
  - `fits_cargo`
  - `broker_fees_unit`
  - `total_fees_unit`
  - `isk_per_jump`

## Separation of concerns
- `routes/` contains HTTP surface only
- `services/` contains ESI access, ingest, logistics, opportunities, export, scheduler, and settings logic
- `db/` contains database setup and models
- `ui/` contains the browser dashboard HTML

## Railway variables
- DATABASE_URL
- ESI_CLIENT_ID
- ESI_CLIENT_SECRET
- ESI_CALLBACK_URL
- PUBLIC_BASE_URL
- TRACKED_REGIONS
- DEFAULT_REGION_HUB_SYSTEMS
- ESI_USER_AGENT
- ENABLE_SCHEDULER
- SCHEDULER_INTERVAL_SECONDS

## Key routes
- `/dashboard`
- `POST /market/ingest`
- `GET /market/opportunities`
- `GET /export/opportunities.csv`
- `GET /logistics/route`
- `GET /scheduler/status`
- `POST /scheduler/run`

## Notes
- Scheduler is off by default. Turn it on with `ENABLE_SCHEDULER=true`.
- Route-aware logistics uses region hub systems for jump counts.
- Volume is cached per item type in the database.
- v2.10 still uses simplified fee assumptions; it is more realistic than v2.08, not perfect.
