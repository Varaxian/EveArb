from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def list_users() -> dict:
    return {"todo": "list pending/approved users"}
