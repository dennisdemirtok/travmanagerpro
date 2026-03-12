"""TravManager — Auth API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse
from app.core.auth import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.deps import get_db
from app.models.user import User
from app.models.stable import Stable
from app.services import stable_service, game_init_service

router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check unique
    existing = await db.execute(select(User).where((User.email == req.email) | (User.username == req.username)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Anvandare med den e-posten eller anvandnamnet finns redan")

    # Ensure game is initialized
    await game_init_service.get_or_create_game_state(db)

    result = await stable_service.create_new_player(db, req.username, req.email, req.password, req.stable_name)

    access = create_access_token(result["user_id"])
    refresh = create_refresh_token(result["user_id"])

    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": {"id": result["user_id"], "username": req.username},
        "stable": {"id": result["stable_id"], "name": result["stable_name"]},
    }


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where((User.username == req.username) | (User.email == req.username))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Fel anvandarnamn eller losenord")

    stable_result = await db.execute(select(Stable).where(Stable.user_id == user.id))
    stable = stable_result.scalar_one_or_none()

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))

    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": {"id": str(user.id), "username": user.username},
        "stable": {"id": str(stable.id), "name": stable.name} if stable else None,
    }


@router.post("/refresh")
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Ogiltig refresh-token")

    access = create_access_token(payload["sub"])
    return {"access_token": access}
