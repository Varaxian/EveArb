# EVE Arb v2.04

This build keeps the working v2.03 base and adds the full next layer:
- CSV export
- scheduler endpoints and optional background scheduler
- route-aware logistics using ESI route jumps
- minimal browser dashboard

## Separation of concerns
- `routes/` contains HTTP surface only
- `services/` contains ESI access, ingest, opportunities, export, scheduler, and settings logic
- `db/` contains database setup and models
- `ui/` contains the basic dashboard HTML

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
- `GET /scheduler/status`
- `POST /scheduler/run`

## Notes
- Scheduler is off by default. Turn it on with `ENABLE_SCHEDULER=true`.
- Route-aware logistics uses region hub systems for jump counts.
- Volume is cached per item type in the database.
