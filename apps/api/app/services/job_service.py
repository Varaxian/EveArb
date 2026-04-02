from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import JobRun

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

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

def job_is_running(db: Session, job_name: str) -> bool:
    row = latest_job(db, job_name)
    return bool(row and row.status == "running")

def latest_job_by_status(db: Session, job_name: str, status: str) -> JobRun | None:
    return (
        db.query(JobRun)
        .filter(JobRun.job_name == job_name, JobRun.status == status)
        .order_by(JobRun.started_at.desc())
        .first()
    )
