from fastapi import APIRouter

router = APIRouter()

@router.get("/repeated-listings")
async def repeated_listings() -> dict:
    return {"todo": "return recurring listing analytics"}
