from fastapi import APIRouter

router = APIRouter()

@router.post("/market")
async def refresh_market() -> dict:
    return {"todo": "trigger market ingest job"}

@router.post("/loads")
async def rebuild_loads() -> dict:
    return {"todo": "trigger load rebuild from latest snapshot"}
