from __future__ import annotations

from fastapi import APIRouter, Depends

from app.services.auth_service import require_admin
from app.services.scheduler_service import ingest_status, run_ingest_cycle, scheduler_state

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status")
def scheduler_status(current_user = Depends(require_admin)):
    return {
        "scheduler": scheduler_state(),
        **ingest_status(),
    }


@router.post("/run")
async def scheduler_run_now(current_user = Depends(require_admin)):
    return await run_ingest_cycle()
