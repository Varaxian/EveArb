# EveArb v2.12

This build advances the live v2.11 baseline with lower-cost location handling.

## Added in v2.12
- best buy and best sell location IDs are persisted into market snapshots
- new local `location_name_cache` table for station/structure name caching
- NPC station names are warmed and stored during ingest
- Upwell structure names are resolved lazily only for surviving opportunity candidates
- unresolved structures are still omitted from results
- request-time live orderbook lookups were removed from opportunities to reduce ESI usage and hosting cost
- runtime schema upgrade helper adds new snapshot location columns automatically on startup

## Existing behavior retained
- Buy Location and Sell Location columns on the dashboard
- cargo realism and fits-cargo truth logic
- profit realism with broker fee, sales tax, and hauling assumptions
- route-security-aware opportunity filtering

## Operational note
After deploying v2.12, run a fresh market ingest so the newest snapshots include persisted location IDs. Older snapshots created before v2.12 may not have those IDs and can produce fewer results until new data is ingested.

## Key routes
- `/dashboard`
- `POST /market/ingest`
- `GET /market/opportunities`
- `GET /export/opportunities.csv`
- `GET /logistics/route`
- `GET /scheduler/status`
- `POST /scheduler/run`
