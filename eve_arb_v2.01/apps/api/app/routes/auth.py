from fastapi import APIRouter

router = APIRouter()

@router.get("/eve/login")
async def eve_login() -> dict:
    return {"todo": "redirect user to EVE SSO"}

@router.get("/eve/callback")
async def eve_callback() -> dict:
    return {"todo": "exchange code, create/update local user, set session"}
