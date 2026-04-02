# eve_arb_v2.01

Railway-ready, GitHub-ready monorepo starter for the EVE load-management platform.

## Goals in v2.01
- Clean monorepo separation
- Railway deploy readiness
- Cost-optimized worker strategy
- GitHub repository ready
- Keep frontend free-tier friendly

## Recommended hosting
- **API**: Railway
- **Postgres**: Railway Postgres
- **Worker**: either Railway worker **or** GitHub Actions cron / manual trigger
- **Web**: Vercel free tier

## Cost-optimized recommendation
Use Railway for:
- Postgres
- API

Use **GitHub Actions** for scheduled worker runs, or call the worker manually from the API.
That keeps you close to the minimum monthly spend.

## Repo structure
```text
apps/
  api/      FastAPI API
  worker/   market ingestion + rebuild jobs
  web/      Next.js frontend scaffold

packages/
  core/     shared calculation logic
  db/       DB models and queries
  esi/      ESI client helpers
  auth/     EVE SSO + session helpers
  utils/    shared utilities

infra/
  docker/   Dockerfiles
  railway/  Railway config templates
```

## Local development

### API + worker dependencies
```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ./packages/utils -e ./packages/auth -e ./packages/esi -e ./packages/db -e ./packages/core -e ./apps/api -e ./apps/worker
```

### API
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir apps/api
```

### Worker (run once)
```bash
python apps/worker/worker.py --mode run_once
```

### Worker (loop, only if you really want it)
```bash
python apps/worker/worker.py --mode loop
```

### Web
```bash
cd apps/web
npm install
npm run dev
```

## Railway deployment

### Service 1: API
Create a Railway service from this repo:
- Root directory: `.`
- Dockerfile path: `infra/docker/api.Dockerfile`
- Start command is already embedded in the Dockerfile

Required env vars:
- `DATABASE_URL`
- `REDIS_URL` (optional if you use it)
- `EVE_SSO_CLIENT_ID`
- `EVE_SSO_CLIENT_SECRET`
- `EVE_SSO_REDIRECT_URI`
- `SESSION_SECRET`
- `ESI_USER_AGENT`

### Service 2: Worker (optional on Railway)
If you want a Railway worker:
- Root directory: `.`
- Dockerfile path: `infra/docker/worker.Dockerfile`

For lowest cost, do **not** keep the worker as an always-on loop.
Use either:
- `WORKER_MODE=run_once` and trigger it manually
- GitHub Actions cron
- Railway cron/job if you later choose to use it

### Database
Provision Railway Postgres and inject `DATABASE_URL`.

## GitHub Actions worker
A workflow is included at:
- `.github/workflows/worker-cron.yml`

It supports:
- manual dispatch
- scheduled cron

Set GitHub secrets:
- `DATABASE_URL`
- `REDIS_URL`
- `ESI_USER_AGENT`
- `EVE_SSO_CLIENT_ID`
- `EVE_SSO_CLIENT_SECRET`
- `EVE_SSO_REDIRECT_URI`
- `SESSION_SECRET`

## Versioning
- Major changes: `v2.0`, `v3.0`, `v4.0`
- Incremental within a major: `v2.01`, `v2.02`, `v2.03`

## Current state
v2.01 is a deploy-prep structure, not the full finished product. It is the correct base for:
- EVE SSO login + admin approval
- market ingestion
- load board
- recurring listing analytics
- courier profitability planning
