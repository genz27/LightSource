from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from app.api.utils import api_error
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.services.auth import decode_token
from app.services.persistence import get_user_by_id
from app.schemas import UserOut


async def get_current_user(
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Missing token"))
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token, token_type="access")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Invalid token"))
    user_id = payload.get("sub")
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Invalid token"))
    return user


async def get_current_user_optional(
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
) -> UserOut | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token, token_type="access")
    except ValueError:
        return None
    user_id = payload.get("sub")
    return await get_user_by_id(session, user_id)
