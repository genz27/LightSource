from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.utils import api_error
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps.auth import get_current_user
from app.schemas import WalletOut, WalletTxOut, TopUpRequest, DeductRequest, PreferencesOut, PreferencesUpdate, TransactionType
from app.services.persistence import get_wallet_by_user_id, list_wallet_txs, change_balance
from app.services.store import get_store


router = APIRouter()


@router.get("/wallet", response_model=WalletOut)
async def get_wallet(current_user = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> WalletOut:
    return await get_wallet_by_user_id(session, current_user.id)


@router.get("/transactions", response_model=list[WalletTxOut])
async def get_transactions(current_user = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> list[WalletTxOut]:
    return await list_wallet_txs(session, current_user.id)


@router.post("/topup", response_model=WalletOut)
async def topup(payload: TopUpRequest, current_user = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> WalletOut:
    w, _ = await change_balance(session, user_id=current_user.id, delta=float(payload.amount), tx_type=TransactionType.TOPUP)
    return w


@router.post("/deduct", response_model=WalletOut)
async def deduct(payload: DeductRequest, current_user = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> WalletOut:
    w, _ = await change_balance(session, user_id=current_user.id, delta=-float(payload.amount), tx_type=TransactionType.DEDUCT, ref_job_id=payload.ref_job_id, description=payload.description)
    return w


@router.get("/prices")
async def get_prices() -> dict:
    store = get_store()
    return store.get_prices()