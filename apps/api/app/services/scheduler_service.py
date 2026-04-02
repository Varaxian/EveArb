from __future__ import annotations

import asyncio
import contextlib

from app.config import settings
from app.db.database import SessionLocal
from app.services.job_service import finish_job, job_is_running, latest_job, start_job
from app.services.market_service import ingest_regions
from app.services.settings_service import get_platform_tracked_regions

_scheduler_task: asyncio.Task | None = None
_scheduler_lock = asyncio.Lock()

async def run_ingest_cycle() -> dict:
    async with _scheduler_lock:
        db = SessionLocal()
        job = None
        try:
            if job_is_running(db, "market_ingest"):
                latest = latest_job(db, "market_ingest")
                return {
                    "status": "skipped",
                    "reason": "market_ingest already running",
                    "job_id": latest.id if latest else None,
                }

            region_ids = get_platform_tracked_regions(db)
            job = start_job(db, "market_ingest", {"region_ids": region_ids})
            result = await ingest_regions(db, region_ids)
            finish_job(db, job.id, "success", result)
            return {"status": "success", "job_id": job.id, "result": result}
        except Exception as exc:
            if job is not None:
                finish_job(db, job.id, "failed", {"error": repr(exc)})
            raise
        finally:
            db.close()

async def scheduler_loop():
    while True:
        try:
            await run_ingest_cycle()
        except Exception as exc:
            print(f"scheduler cycle error: {exc!r}")
        await asyncio.sleep(settings.scheduler_interval_seconds)

def start_scheduler():
    global _scheduler_task
    if not settings.enable_scheduler:
        return
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(scheduler_loop())

async def stop_scheduler():
    global _scheduler_task
    if _scheduler_task is not None:
        _scheduler_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _scheduler_task
        _scheduler_task = None

def scheduler_state() -> dict:
    return {
        "enabled": settings.enable_scheduler,
        "task_running": bool(_scheduler_task and not _scheduler_task.done()),
        "interval_seconds": settings.scheduler_interval_seconds,
    }


async def restart_scheduler() -> dict:
    await stop_scheduler()
    start_scheduler()
    return scheduler_state()
