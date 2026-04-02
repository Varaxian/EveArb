# EVE Arb v2.02

This build keeps the clean Railway-safe baseline and adds the first ESI auth layer.

## Included
- Railway-safe Dockerfile using `${PORT:-8000}`
- FastAPI app shell
- `/auth/login`
- `/auth/callback`
- `/config-check`
- `.env.example` with the Railway public callback URL pattern

## Railway env vars to set
- `ESI_CLIENT_ID`
- `ESI_CLIENT_SECRET`
- `ESI_CALLBACK_URL=https://evearb-production.up.railway.app/auth/callback`
- `PUBLIC_BASE_URL=https://evearb-production.up.railway.app`

## Test after deploy
- `/`
- `/health`
- `/config-check`
- `/auth/login`

## Notes
This version does not persist tokens yet. It is the auth scaffold so login can complete cleanly before we add
market pull, storage, opportunities, CSV, and logistics.
