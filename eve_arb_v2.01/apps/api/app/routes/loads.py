from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def get_loads() -> dict:
    return {"todo": "return load board rows"}
