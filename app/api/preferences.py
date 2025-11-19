from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps.auth import get_current_user
from app.schemas import PreferencesOut, PreferencesUpdate
from app.services.persistence import get_preferences, update_preferences


router = APIRouter()


@router.get("/me", response_model=PreferencesOut)
async def get_me_preferences(current_user = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> PreferencesOut:
    return await get_preferences(session, current_user.id)


@router.put("/me", response_model=PreferencesOut)
async def put_me_preferences(payload: PreferencesUpdate, current_user = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> PreferencesOut:
    return await update_preferences(session, user_id=current_user.id, theme=payload.theme, language=payload.language, notifications=payload.notifications, meta=payload.meta)