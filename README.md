# EveArb v2.14

This build advances the live v2.13 baseline with a streaming global-ingest refactor.

## Added in v2.14
- region market ingest now streams ESI order pages instead of loading full regions into memory
- aggregation happens incrementally page-by-page
- global dataset architecture remains intact for all users
- manual ingest keeps the v2.13 hard timeout protection

## Why this matters
- flatter memory usage during ingest
- lower OOM risk on Railway
- safer foundation for multi-user shared-market architecture
- prepares the app for future scheduled global ingests

## Existing behavior retained
- best buy and best sell location IDs persist into market snapshots
- local location cache remains in place
- Buy Location and Sell Location remain on opportunities
- unresolved structures are omitted from results
- cargo realism and fits-cargo truth logic remain intact
- profit realism with broker fee, sales tax, and hauling assumptions remains intact

## Next logical layer
- user-saved Active Opportunities
- Completed / Failed status workflow
- fail-reason dropdown analytics on saved opportunity snapshots

## Operational note
After deploying v2.14, global market ingest should use much less memory than earlier builds while keeping the same shared-data behavior.
