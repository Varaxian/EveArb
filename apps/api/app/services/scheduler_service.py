from __future__ import annotations

import asyncio
import contextlib

from app.config import settings
from app.db.database import SessionLocal
from app.services.job_service import (
    finish_job,
    is_stale,
    latest_job,
    latest_job_by_status,
    mark_stale_jobs_failed,
    parse_details_json,
    start_job,
)
from app.services.market_service import ingest_regions
from app.services.settings_service import get_platform_tracked_regions

_scheduler_task: asyncio.Task | None = None
_active_ingest_task: asyncio.Task | None = None
_scheduler_lock = asyncio.Lock()
INGEST_JOB_NAMES = ["market_ingest", "manual_market_ingest"]


def _cleanup_finished_task() -> None:
    global _active_ingest_task
    if _active_ingest_task is not None and _active_ingest_task.done():
        _active_ingest_task = None


def _latest_ingest_job(db):
    candidates = []
    for name in INGEST_JOB_NAMES:
        row = latest_job(db, name)
        if row is not None:
            candidates.append(row)
    if not candidates:
        return None
    return sorted(candidates, key=lambda x: (x.started_at or x.finished_at), reverse=True)[0]


def _running_ingest_job(db):
    mark_stale_jobs_failed(db, INGEST_JOB_NAMES, settings.ingest_stale_seconds)
    candidates = []
    for name in INGEST_JOB_NAMES:
        row = latest_job(db, name)
        if row is not None and row.status == "running":
            candidates.append(row)
    if not candidates:
        return None
    return sorted(candidates, key=lambda x: (x.started_at or x.finished_at), reverse=True)[0]


async def _execute_ingest_job(job_name: str, region_ids: list[int], details: dict | None = None) -> dict:
    db = SessionLocal()
    job = None
    try:
        job = start_job(db, job_name, details or {"region_ids": region_ids})
        result = await asyncio.wait_for(
            ingest_regions(db, region_ids),
            timeout=settings.manual_ingest_timeout_seconds,
        )
        finish_job(db, job.id, "success", result)
        return {"status": "success", "job_id": job.id, "result": result}
    except asyncio.TimeoutError:
        if job is not None:
            finish_job(
                db,
                job.id,
                "failed",
                {"error": f"{job_name} timed out after {settings.manual_ingest_timeout_seconds} seconds"},
            )
        return {"status": "failed", "job_id": job.id if job else None, "error": "timeout"}
    except Exception as exc:
        if job is not None:
            finish_job(db, job.id, "failed", {"error": repr(exc)})
        raise
    finally:
        db.close()


async def run_ingest_cycle() -> dict:
    async with _scheduler_lock:
        _cleanup_finished_task()
        db = SessionLocal()
        try:
            running = _running_ingest_job(db)
            if running is not None or (_active_ingest_task is not None and not _active_ingest_task.done()):
                return {
                    "status": "skipped",
                    "reason": "market ingest already running",
                    "job_id": running.id if running else None,
                }
            region_ids = get_platform_tracked_regions(db)
        finally:
            db.close()
    return await _execute_ingest_job("market_ingest", region_ids, {"region_ids": region_ids, "trigger": "scheduler"})


async def launch_manual_ingest(region_ids: list[int], actor_user_id: int | None = None) -> dict:
    global _active_ingest_task
    async with _scheduler_lock:
        _cleanup_finished_task()
        db = SessionLocal()
        try:
            running = _running_ingest_job(db)
            if running is not None or (_active_ingest_task is not None and not _active_ingest_task.done()):
                return {
                    "status": "already_running",
                    "job_id": running.id if running else None,
                }
            trigger_details = {"region_ids": region_ids, "trigger": "manual"}
            if actor_user_id is not None:
                trigger_details["actor_user_id"] = actor_user_id
            _active_ingest_task = asyncio.create_task(_execute_ingest_job("manual_market_ingest", region_ids, trigger_details))
            return {"status": "started", "region_ids": region_ids}
        finally:
            db.close()


def ingest_status() -> dict:
    _cleanup_finished_task()
    db = SessionLocal()
    try:
        running = _running_ingest_job(db)
        latest = _latest_ingest_job(db)
        latest_success = latest_job_by_status(db, "market_ingest", "success") or latest_job_by_status(db, "manual_market_ingest", "success")
        latest_failed = latest_job_by_status(db, "market_ingest", "failed") or latest_job_by_status(db, "manual_market_ingest", "failed")

        def _pack(row):
            if not row:
                return None
            return {
                "id": row.id,
                "job_name": row.job_name,
                "status": row.status,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "finished_at": row.finished_at.isoformat() if row.finished_at else None,
                "details": parse_details_json(row.details_json),
                "is_stale": is_stale(row, settings.ingest_stale_seconds),
            }

        return {
            "ingest_task_running": bool(_active_ingest_task and not _active_ingest_task.done()),
            "current_running_job": _pack(running),
            "latest_job": _pack(latest),
            "latest_successful_market_ingest": _pack(latest_success),
            "latest_failed_market_ingest": _pack(latest_failed),
        }
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
    _cleanup_finished_task()
    return {
        "enabled": settings.enable_scheduler,
        "task_running": bool(_scheduler_task and not _scheduler_task.done()),
        "interval_seconds": settings.scheduler_interval_seconds,
        "ingest_task_running": bool(_active_ingest_task and not _active_ingest_task.done()),
        "manual_ingest_timeout_seconds": settings.manual_ingest_timeout_seconds,
        "ingest_stale_seconds": settings.ingest_stale_seconds,
    }
