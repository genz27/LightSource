from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.utils import api_error

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User as UserModel
from app.schemas import AuthRequest, AuthResponse, PasswordChange, UserOut, RegisterRequest
from app.services.auth import create_tokens, decode_token, hash_password, verify_password
from app.services.persistence import count_users, create_user_db, get_user_by_email, get_user_by_id
from app.deps.auth import get_current_user

router = APIRouter()


@router.post("/login", response_model=AuthResponse)
async def login(payload: AuthRequest, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    user = await get_user_by_email(session, payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Invalid credentials"))
    db_user = await session.get(UserModel, user.id)
    if not db_user or not verify_password(payload.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Invalid credentials"))
    access, refresh = create_tokens(user.id)
    return AuthResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=900,
        issued_at=dt.datetime.utcnow(),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_session)) -> UserOut:
    existing = await get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("email already exists"))
    total_users = await count_users(session)
    role = "admin" if total_users == 0 else "user"
    user = await create_user_db(session, email=payload.email, username=payload.username, password_hash=hash_password(payload.password), role=role)
    return user


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    try:
        payload = decode_token(refresh_token, token_type="refresh")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Invalid refresh token"))
    user_id = payload.get("sub")
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Invalid refresh token"))
    access, new_refresh = create_tokens(user_id)
    return AuthResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=900,
        issued_at=dt.datetime.utcnow(),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChange,
    session: AsyncSession = Depends(get_session),
    current_user: UserOut = Depends(get_current_user),
) -> None:
    db_user = await session.get(UserModel, current_user.id)
    if not db_user or not verify_password(payload.old_password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Old password incorrect"))
    db_user.password_hash = hash_password(payload.new_password)
    await session.commit()
