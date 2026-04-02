# EveArb v2.11

This build advances the live v2.10 baseline with named trade locations on opportunities.

## Added in v2.11
- Buy Location column on opportunities
- Sell Location column on opportunities
- strict omission of opportunities where either location cannot be resolved
- NPC station name resolution through ESI name lookup
- Upwell structure resolution attempted with the authenticated character token when available
- unresolved structures are omitted entirely from the opportunity list per product requirement

## Existing v2.10 behavior retained
- corrected fits-cargo truth logic
- cargo realism on opportunities
- user setting for total m3 available
- per-opportunity total m3 necessary + fits cargo
- profit realism pass with broker fee + sales tax + hauling cost assumptions
- route security filter options aligned with backend

## Important implementation note
This version resolves named buy/sell locations at opportunity-build time using live orderbooks so it can be deployed without requiring a schema migration on the existing database.

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
- Opportunities with unresolved buy or sell locations are excluded from results.
