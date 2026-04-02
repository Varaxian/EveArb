# EveArb v2.13

This build advances the live v2.12 baseline with a manual-ingest stall-risk reduction pass.

## Added in v2.13
- hard 120-second timeout around manual ingest requests
- manual ingest now returns a 504 timeout instead of sitting at "Running..." indefinitely
- removed synchronous NPC cache warming from the ingest request path to reduce ESI/network stall risk

## Existing v2.12 behavior retained
- best buy and best sell location IDs persist into market snapshots
- local `location_name_cache` table remains in place
- NPC station names can still resolve through the cache layer when needed
- Upwell structure names are resolved lazily only for surviving opportunity candidates
- unresolved structures are omitted from results
- request-time live orderbook lookups remain removed from the opportunities path

## Operational note
After deploying v2.13, manual ingest should return faster and fail more honestly. If location names are missing for newer station IDs, they can still be resolved later through the existing location-cache path without blocking ingest.

## Key routes
- `/dashboard`
- `POST /market/ingest`
- `GET /market/opportunities`
- `GET /export/opportunities.csv`
- `GET /logistics/route`
- `GET /scheduler/status`
- `POST /scheduler/run`
