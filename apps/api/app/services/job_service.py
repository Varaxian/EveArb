from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import JobRun

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def parse_details_json(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw, "invalid_json": True}

def start_job(db: Session, job_name: str, details: dict | None = None) -> JobRun:
    row = JobRun(
        job_name=job_name,
        status="running",
        started_at=utcnow(),
        details_json=json.dumps(details or {}),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def finish_job(db: Session, job_id: int, status: str, details: dict | None = None) -> JobRun | None:
    row = db.query(JobRun).filter(JobRun.id == job_id).first()
    if row is None:
        return None
    row.status = status
    row.finished_at = utcnow()
    row.details_json = json.dumps(details or {})
    db.commit()
    db.refresh(row)
    return row

def latest_job(db: Session, job_name: str) -> JobRun | None:
    return db.query(JobRun).filter(JobRun.job_name == job_name).order_by(JobRun.started_at.desc()).first()

def latest_jobs(db: Session, job_names: list[str], limit: int = 10) -> list[JobRun]:
    return (
        db.query(JobRun)
        .filter(JobRun.job_name.in_(job_names))
        .order_by(JobRun.started_at.desc())
        .limit(limit)
        .all()
    )

def is_stale(row: JobRun | None, stale_seconds: int) -> bool:
    if row is None or row.status != "running" or row.started_at is None:
        return False
    age = (utcnow() - row.started_at).total_seconds()
    return age > stale_seconds

def job_is_running(db: Session, job_name: str, stale_seconds: int | None = None) -> bool:
    row = latest_job(db, job_name)
    if stale_seconds and is_stale(row, stale_seconds):
        return False
    return bool(row and row.status == "running")

def latest_job_by_status(db: Session, job_name: str, status: str) -> JobRun | None:
    return (
        db.query(JobRun)
        .filter(JobRun.job_name == job_name, JobRun.status == status)
        .order_by(JobRun.started_at.desc())
        .first()
    )

def mark_stale_jobs_failed(db: Session, job_names: list[str], stale_seconds: int) -> list[int]:
    rows = (
        db.query(JobRun)
        .filter(JobRun.job_name.in_(job_names), JobRun.status == "running")
        .order_by(JobRun.started_at.desc())
        .all()
    )
    failed_ids: list[int] = []
    now = utcnow()
    for row in rows:
        if row.started_at is None:
            continue
        age = (now - row.started_at).total_seconds()
        if age <= stale_seconds:
            continue
        details = parse_details_json(row.details_json) or {}
        if not isinstance(details, dict):
            details = {"details": details}
        details.update(
            {
                "error": f"job marked stale after {stale_seconds} seconds",
                "stale_seconds": stale_seconds,
            }
        )
        row.status = "failed"
        row.finished_at = now
        row.details_json = json.dumps(details)
        failed_ids.append(row.id)
    if failed_ids:
        db.commit()
    return failed_ids
