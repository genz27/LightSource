from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_session
from app.deps.auth import get_current_user
from app.schemas import (
    UserOut,
    ProviderInfo,
    WalletOut,
    WalletTxOut,
    JobOut,
    AssetOut,
    AdminCreateUser,
    AdminRoleUpdate,
    AdminUserUpdate,
    AdminWalletAdjust,
    AdminPasswordReset,
    TransactionType,
)
from app.services.persistence import (
    list_users_db,
    list_users_db as _list_users,
    create_user_db,
    update_user_role,
    update_user_fields,
    update_user_password,
    delete_user_db,
    list_wallets_db,
    list_wallets_filtered,
    get_wallet_by_user_id,
    list_wallet_txs,
    change_balance,
    list_jobs_db,
    list_jobs_filtered,
    list_assets_db,
    list_assets_filtered,
    add_provider_db,
    delete_provider_db,
    get_provider_by_name,
    update_asset_fields,
    provider_model_to_info,
)
from app.schemas import JobKind, AssetType
from app.services.metrics import metrics
from app.services.store import get_store
from app.schemas import JobStatus
from app.services.auth import hash_password
from app.api.utils import api_error
from app.services import audit as audit_service


router = APIRouter()


def _ensure_admin(current_user: UserOut) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


# Users
@router.get("/users", response_model=list[UserOut])
async def admin_list_users(
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    q: str | None = Query(None, description="search by email/username contains"),
) -> list[UserOut]:
    _ensure_admin(current_user)
    offset = (page - 1) * limit
    # basic filter inline without new persistence
    users = await _list_users(session, offset=offset, limit=limit)
    if role:
        users = [u for u in users if u.role == role]
    if q:
        ql = q.lower()
        users = [u for u in users if (u.email.lower().find(ql) >= 0 or u.username.lower().find(ql) >= 0)]
    return users


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def admin_create_user(payload: AdminCreateUser, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> UserOut:
    _ensure_admin(current_user)
    return await create_user_db(session, email=payload.email, username=payload.username, password_hash=hash_password(payload.password), role=payload.role)


@router.get("/users/{user_id}", response_model=UserOut)
async def admin_get_user(user_id: str, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> UserOut:
    _ensure_admin(current_user)
    from app.services.persistence import get_user_by_id
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("User not found"))
    return user


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def admin_patch_user_role(user_id: str, payload: AdminRoleUpdate, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> UserOut:
    _ensure_admin(current_user)
    user = await update_user_role(session, user_id=user_id, role=payload.role)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("User not found"))
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def admin_patch_user(user_id: str, payload: AdminUserUpdate, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> UserOut:
    _ensure_admin(current_user)
    user = await update_user_fields(session, user_id=user_id, email=payload.email, username=payload.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("User not found"))
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(user_id: str, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> None:
    _ensure_admin(current_user)
    ok = await delete_user_db(session, user_id=user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("User not found"))


@router.post("/users/{user_id}/reset-password", response_model=UserOut)
async def admin_reset_password(user_id: str, payload: AdminPasswordReset, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> UserOut:
    _ensure_admin(current_user)
    user = await update_user_password(session, user_id=user_id, password_hash=hash_password(payload.new_password))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("User not found"))
    return user


# Wallets
@router.get("/wallets", response_model=list[WalletOut])
async def admin_list_wallets(
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    currency: str | None = Query(None),
    balance_min: float | None = Query(None),
    balance_max: float | None = Query(None),
    updated_after: str | None = Query(None, description="ISO time"),
) -> list[WalletOut]:
    _ensure_admin(current_user)
    offset = (page - 1) * limit
    dt_after = None
    try:
        if updated_after:
            from datetime import datetime
            dt_after = datetime.fromisoformat(updated_after)
    except Exception:
        dt_after = None
    return await list_wallets_filtered(session, currency=currency, balance_min=balance_min, balance_max=balance_max, updated_after=dt_after, offset=offset, limit=limit)


@router.get("/wallets/{user_id}", response_model=WalletOut)
async def admin_get_wallet(user_id: str, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> WalletOut:
    _ensure_admin(current_user)
    return await get_wallet_by_user_id(session, user_id)


@router.get("/wallets/{user_id}/transactions", response_model=list[WalletTxOut])
async def admin_get_wallet_txs(
    user_id: str,
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
) -> list[WalletTxOut]:
    _ensure_admin(current_user)
    offset = (page - 1) * limit
    return await list_wallet_txs(session, user_id, offset=offset, limit=limit)


@router.post("/wallets/{user_id}/adjust", response_model=WalletOut)
async def admin_wallet_adjust(user_id: str, payload: AdminWalletAdjust, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> WalletOut:
    _ensure_admin(current_user)
    w, _ = await change_balance(session, user_id=user_id, delta=float(payload.amount), tx_type=TransactionType.ADJUST, description=payload.description)
    return w


# Jobs
@router.get("/jobs", response_model=list[JobOut])
async def admin_list_jobs(
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: JobStatus | None = Query(None),
    kind: JobKind | None = Query(None),
    owner_id: str | None = Query(None),
    created_from: str | None = Query(None),
    created_to: str | None = Query(None),
) -> list[JobOut]:
    _ensure_admin(current_user)
    offset = (page - 1) * limit
    from datetime import datetime
    dt_from = datetime.fromisoformat(created_from) if created_from else None
    dt_to = datetime.fromisoformat(created_to) if created_to else None
    kind_db = None
    if kind is not None:
        from app.models.job import JobKindDB as JKDB
        kind_db = JKDB(kind.value)
    return await list_jobs_filtered(session, status=status, kind=kind_db, owner_id=owner_id, created_from=dt_from, created_to=dt_to, offset=offset, limit=limit)


@router.post("/jobs/{job_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def admin_cancel_job(job_id: str, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> None:
    _ensure_admin(current_user)
    from app.models.job import Job as JobModel
    job = await session.get(JobModel, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Job not found"))
    from app.services.persistence import update_job_fields
    await update_job_fields(session, job_id, status=JobStatus.CANCELED)
    store = get_store()
    if store.get_job(job_id):
        store.update_job(job_id, status=JobStatus.CANCELED)


# Assets
@router.get("/assets", response_model=list[AssetOut])
async def admin_list_assets(
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    type: AssetType | None = Query(None),
    provider: str | None = Query(None),
    public: bool | None = Query(None),
    owner_id: str | None = Query(None),
) -> list[AssetOut]:
    _ensure_admin(current_user)
    offset = (page - 1) * limit
    return await list_assets_filtered(session, asset_type=type, provider=provider, public_only=public, owner_id=owner_id, offset=offset, limit=limit)


@router.patch("/assets/{asset_id}", response_model=AssetOut)
async def admin_patch_asset(asset_id: str, public: bool, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> AssetOut:
    _ensure_admin(current_user)
    updated = await update_asset_fields(session, asset_id, is_public=public)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Asset not found"))
    return updated


# Providers
@router.post("/providers", response_model=ProviderInfo, status_code=status.HTTP_201_CREATED)
async def admin_create_provider(payload: dict, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> ProviderInfo:
    _ensure_admin(current_user)
    name = payload.get("name")
    display_name = payload.get("display_name")
    models = payload.get("models") or []
    capabilities = payload.get("capabilities") or []
    if not name or not display_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("name and display_name required"))
    return await add_provider_db(session, name=name, display_name=display_name, models=models, capabilities=capabilities, enabled=bool(payload.get("enabled", True)), notes=payload.get("notes"), base_url=payload.get("base_url"))


@router.get("/providers/{name}", response_model=ProviderInfo)
async def admin_get_provider(name: str, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> ProviderInfo:
    _ensure_admin(current_user)
    p = await get_provider_by_name(session, name)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Provider not found"))
    return provider_model_to_info(p)


@router.delete("/providers/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_provider(name: str, current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> None:
    _ensure_admin(current_user)
    ok = await delete_provider_db(session, name=name)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Provider not found"))


# Metrics
@router.get("/metrics")
async def admin_metrics(current_user: UserOut = Depends(get_current_user)) -> dict:
    _ensure_admin(current_user)
    return metrics.snapshot()


# Audit logs
@router.get("/audit/logs")
async def admin_audit_logs(
    current_user: UserOut = Depends(get_current_user),
    event: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    since: float | None = Query(None, description="timestamp seconds"),
    until: float | None = Query(None, description="timestamp seconds"),
) -> list[dict]:
    _ensure_admin(current_user)
    offset = (page - 1) * limit
    return audit_service.read(event=event, since=since, until=until, offset=offset, limit=limit)


# Runtime config
@router.get("/config")
async def admin_get_config(current_user: UserOut = Depends(get_current_user)) -> dict:
    _ensure_admin(current_user)
    store = get_store()
    return {"debug": store.get_debug(), "prices": store.get_prices()}


@router.patch("/config")
async def admin_patch_config(payload: dict, current_user: UserOut = Depends(get_current_user)) -> dict:
    _ensure_admin(current_user)
    store = get_store()
    if "debug" in payload:
        store.set_debug(bool(payload.get("debug")))
        try:
            audit_service.write("admin.config.debug", {"user_id": current_user.id, "debug": store.get_debug()})
        except Exception:
            pass
    if "prices" in payload:
        store.set_prices(payload.get("prices"))
        try:
            audit_service.write("admin.config.prices", {"user_id": current_user.id, "prices": store.get_prices()})
        except Exception:
            pass
    return {"debug": store.get_debug(), "prices": store.get_prices()}


# Exports (CSV)
@router.get("/export/users", response_class=PlainTextResponse)
async def admin_export_users(current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> str:
    _ensure_admin(current_user)
    rows = await list_users_db(session)
    out = ["id,email,username,role,created_at"]
    for u in rows:
        out.append(f"{u.id},{u.email},{u.username},{u.role},{u.created_at.isoformat()}Z")
    return "\n".join(out)


@router.get("/export/jobs", response_class=PlainTextResponse)
async def admin_export_jobs(current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> str:
    _ensure_admin(current_user)
    rows = await list_jobs_db(session)
    out = ["id,kind,status,progress,owner_id,created_at,updated_at"]
    for j in rows:
        out.append(f"{j.id},{j.kind.value},{j.status.value},{j.progress},{j.owner_id or ''},{j.created_at.isoformat()}Z,{j.updated_at.isoformat()}Z")
    return "\n".join(out)


@router.get("/export/assets", response_class=PlainTextResponse)
async def admin_export_assets(current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> str:
    _ensure_admin(current_user)
    rows = await list_assets_db(session)
    out = ["id,type,provider,url,public,owner_id,created_at"]
    for a in rows:
        out.append(f"{a.id},{a.type.value},{a.provider or ''},{a.url},{'true' if a.is_public else 'false'},{a.owner_id or ''},{a.created_at.isoformat()}Z")
    return "\n".join(out)


@router.get("/export/wallets", response_class=PlainTextResponse)
async def admin_export_wallets(current_user: UserOut = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> str:
    _ensure_admin(current_user)
    rows = await list_wallets_db(session)
    out = ["owner_id,balance,currency,frozen,updated_at"]
    for w in rows:
        out.append(f"{w.owner_id},{w.balance},{w.currency},{w.frozen},{w.updated_at.isoformat()}Z")
    return "\n".join(out)