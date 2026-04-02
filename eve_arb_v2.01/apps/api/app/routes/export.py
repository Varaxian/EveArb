from fastapi import APIRouter

router = APIRouter()

@router.get("/loads.csv")
async def export_loads_csv() -> dict:
    return {"todo": "export current loads as CSV"}
