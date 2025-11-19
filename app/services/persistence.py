from __future__ import annotations

import datetime as dt
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetTypeDB
from app.models.job import Job, JobKindDB, JobStatusDB
from app.models.provider import Provider
from app.models.user import User
from app.schemas import AssetOut, AssetType, JobOut, JobStatus, ProviderInfo, UserOut, Capability
from app.models.wallet import Wallet, WalletTransaction, WalletTxStatusDB, WalletTxTypeDB
from app.models.preferences import UserPreferences
from app.schemas import WalletOut, WalletTxOut, TransactionType, TransactionStatus, PreferencesOut


def job_model_to_out(model: Job) -> JobOut:
    return JobOut(
        id=model.id,
        prompt=model.prompt,
        kind=model.kind.value,  # type: ignore[arg-type]
        model=model.model,
        provider=model.provider,
        is_public=model.is_public,
        params=model.params,
        status=model.status.value,  # type: ignore[arg-type]
        progress=model.progress,
        asset_id=model.asset_id,
        error=model.error,
        created_at=model.created_at.replace(tzinfo=None),
        updated_at=(model.updated_at.replace(tzinfo=None) if model.updated_at else model.created_at.replace(tzinfo=None)),
        owner_id=model.owner_id,
    )


def asset_model_to_out(model: Asset) -> AssetOut:
    return AssetOut(
        id=model.id,
        type=AssetType(model.type.value),
        provider=model.provider,
        url=model.url,
        preview_url=model.preview_url,
        meta=model.meta,
        is_public=model.is_public,
        created_at=model.created_at.replace(tzinfo=None),
        owner_id=model.owner_id,
    )


def user_model_to_out(model: User) -> UserOut:
    return UserOut(
        id=model.id,
        username=getattr(model, "username", model.email.split("@")[0]),
        email=model.email,
        role=model.role,
        created_at=model.created_at.replace(tzinfo=None),
    )


async def next_job_id(session: AsyncSession) -> str:
    count = await session.scalar(select(func.count()).select_from(Job))
    base = 231
    return f"job_{base + int(count or 0) + 1}"


async def next_asset_id(session: AsyncSession) -> str:
    count = await session.scalar(select(func.count()).select_from(Asset))
    return f"asset_{int(count or 0) + 1}"


async def persist_job(session: AsyncSession, job: JobOut) -> None:
    existing = await session.get(Job, job.id)
    if existing:
        return
    db_obj = Job(
        id=job.id,
        owner_id=job.owner_id,
        prompt=job.prompt,
        kind=JobKindDB(job.kind.value if isinstance(job.kind, JobKindDB) else job.kind),
        model=job.model,
        provider=job.provider,
        is_public=job.is_public,
        params=job.params.dict() if hasattr(job.params, "dict") else job.params,
        status=JobStatusDB(job.status.value if isinstance(job.status, JobStatusDB) else job.status),
        progress=job.progress,
        asset_id=job.asset_id,
        error=job.error,
    )
    session.add(db_obj)
    await session.commit()


async def update_job_fields(session: AsyncSession, job_id: str, **fields) -> None:
    job = await session.get(Job, job_id)
    if not job:
        return
    for key, value in fields.items():
        if key in {"status"} and isinstance(value, JobStatus):
            value = JobStatusDB(value.value)
        setattr(job, key, value)
    job.updated_at = dt.datetime.utcnow()
    await session.commit()


async def list_jobs_db(session: AsyncSession, *, offset: int = 0, limit: int | None = None) -> List[JobOut]:
    stmt = select(Job).order_by(Job.created_at.desc())
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    return [job_model_to_out(j) for j in result]


async def list_jobs_filtered(
    session: AsyncSession,
    *,
    status: JobStatus | None = None,
    kind: JobKindDB | None = None,
    owner_id: str | None = None,
    created_from: dt.datetime | None = None,
    created_to: dt.datetime | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> List[JobOut]:
    stmt = select(Job)
    if status is not None:
        stmt = stmt.where(Job.status == JobStatusDB(status.value))
    if kind is not None:
        stmt = stmt.where(Job.kind == kind)
    if owner_id is not None:
        stmt = stmt.where(Job.owner_id == owner_id)
    if created_from is not None:
        stmt = stmt.where(Job.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(Job.created_at <= created_to)
    stmt = stmt.order_by(Job.created_at.desc())
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    return [job_model_to_out(j) for j in result]


async def get_job_db(session: AsyncSession, job_id: str) -> Optional[JobOut]:
    job = await session.get(Job, job_id)
    return job_model_to_out(job) if job else None


async def persist_asset(
    session: AsyncSession,
    *,
    asset_id: str,
    owner_id: str | None,
    kind: str,
    provider: str | None,
    is_public: bool,
    meta: dict,
    url: str,
    preview_url: str | None,
) -> None:
    existing = await session.get(Asset, asset_id)
    if existing:
        return
    asset = Asset(
        id=asset_id,
        owner_id=owner_id,
        type=AssetTypeDB.IMAGE if kind == "text_to_image" else AssetTypeDB.VIDEO,
        provider=provider,
        url=url,
        preview_url=preview_url,
        meta=meta,
        is_public=is_public,
    )
    session.add(asset)
    await session.commit()


async def list_assets_db(
    session: AsyncSession,
    *,
    asset_type: AssetType | None = None,
    provider: str | None = None,
    public_only: bool | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> List[AssetOut]:
    stmt = select(Asset)
    if asset_type:
        stmt = stmt.where(Asset.type == AssetTypeDB(asset_type.value))
    if provider:
        stmt = stmt.where(Asset.provider == provider)
    if public_only is not None:
        stmt = stmt.where(Asset.is_public == public_only)
    stmt = stmt.order_by(Asset.created_at.desc())
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    return [asset_model_to_out(a) for a in result]


async def list_assets_filtered(
    session: AsyncSession,
    *,
    asset_type: AssetType | None = None,
    provider: str | None = None,
    public_only: bool | None = None,
    owner_id: str | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> List[AssetOut]:
    stmt = select(Asset)
    if asset_type:
        stmt = stmt.where(Asset.type == AssetTypeDB(asset_type.value))
    if provider:
        stmt = stmt.where(Asset.provider == provider)
    if public_only is not None:
        stmt = stmt.where(Asset.is_public == public_only)
    if owner_id:
        stmt = stmt.where(Asset.owner_id == owner_id)
    stmt = stmt.order_by(Asset.created_at.desc())
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    return [asset_model_to_out(a) for a in result]


async def delete_asset_db(session: AsyncSession, asset_id: str) -> bool:
    asset = await session.get(Asset, asset_id)
    if not asset:
        return False
    await session.delete(asset)
    await session.commit()
    return True


# User helpers
async def count_users(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count()).select_from(User)) or 0)


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[UserOut]:
    email = email.lower()
    result = await session.scalars(select(User).where(User.email == email))
    user = result.first()
    return user_model_to_out(user) if user else None


async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[UserOut]:
    user = await session.get(User, user_id)
    return user_model_to_out(user) if user else None


async def create_user_db(session: AsyncSession, *, email: str, username: str, password_hash: str, role: str) -> UserOut:
    user = User(email=email.lower(), username=username, password_hash=password_hash, role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user_model_to_out(user)


# Provider helpers
def provider_model_to_info(model: Provider) -> ProviderInfo:
    return ProviderInfo(
        name=model.name,
        display_name=model.display_name,
        models=model.models or [],
        capabilities=[Capability(c) for c in (model.capabilities or [])],
        enabled=model.enabled,
        notes=model.notes,
        base_url=model.base_url,
    )


async def get_provider_by_name(session: AsyncSession, name: str) -> Provider | None:
    """Return raw Provider ORM object for internal use (includes secrets)."""
    return await session.get(Provider, name)


async def ensure_default_providers(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(Provider))
    if not count or count == 0:
        defaults = [
            Provider(
                name="qwen",
                display_name="Qwen",
                models=["qwen-image", "qwen-image-edit"],
                capabilities=["image"],
                enabled=True,
                notes="Text/Image edit (ModelScope Qwen)",
                base_url="https://api-inference.modelscope.cn/",
            ),
            Provider(
                name="sora2",
                display_name="Sora2",
                models=["sora2-video"],
                capabilities=["video"],
                enabled=True,
                notes="Text/Image to video (landscape/portrait)",
                base_url="https://api.sora2.example",
            ),
        ]
        for p in defaults:
            session.add(p)
        await session.commit()
    else:
        existing = await session.scalars(select(Provider))
        for p in list(existing):
            if p.name == "qwen":
                models = p.models or []
                if "qwen-image-edit" not in models:
                    p.models = models + ["qwen-image-edit"]
        await session.commit()


async def list_providers_db(session: AsyncSession) -> list[ProviderInfo]:
    await ensure_default_providers(session)
    result = await session.scalars(select(Provider).order_by(Provider.name))
    return [provider_model_to_info(p) for p in result]


async def update_provider_db(
    session: AsyncSession,
    *,
    name: str,
    enabled: bool | None = None,
    notes: str | None = None,
    base_url: str | None = None,
    models: list[str] | None = None,
    capabilities: list[str] | None = None,
) -> ProviderInfo | None:
    provider = await session.get(Provider, name)
    if not provider:
        return None
    if enabled is not None:
        provider.enabled = enabled
    if notes is not None:
        provider.notes = notes
    if base_url is not None:
        provider.base_url = base_url
    if models is not None:
        try:
            provider.models = [str(m).strip() for m in (models or []) if str(m).strip()]
        except Exception:
            provider.models = provider.models or []
    if capabilities is not None:
        try:
            caps = [str(c).strip().lower() for c in (capabilities or []) if str(c).strip()]
            allowed = {"image", "video"}
            provider.capabilities = [c for c in caps if c in allowed]
        except Exception:
            provider.capabilities = provider.capabilities or []
    await session.commit()
    await session.refresh(provider)
    return provider_model_to_info(provider)


async def update_provider_secret_db(
    session: AsyncSession,
    *,
    name: str,
    api_token: str | None,
) -> bool:
    """Update provider api_token without exposing it via public schemas."""

    provider = await session.get(Provider, name)
    if not provider:
        return False
    provider.api_token = api_token
    await session.commit()
    return True
async def count_jobs_db(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count()).select_from(Job)) or 0)
async def count_assets_db(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count()).select_from(Asset)) or 0)


# Wallet helpers
def _wallet_model_to_out(w: Wallet) -> WalletOut:
    return WalletOut(
        owner_id=w.user_id,
        balance=float(w.balance or 0),
        currency=w.currency,
        frozen=float(w.frozen or 0),
        updated_at=(w.updated_at.replace(tzinfo=None) if w.updated_at else w.created_at.replace(tzinfo=None)),
    )


def _tx_model_to_out(t: WalletTransaction) -> WalletTxOut:
    return WalletTxOut(
        id=t.id,
        user_id=t.user_id,
        amount=float(t.amount),
        type=TransactionType(t.type.value),
        status=TransactionStatus(t.status.value),
        ref_job_id=t.ref_job_id,
        description=t.description,
        meta=t.meta or {},
        created_at=t.created_at.replace(tzinfo=None),
    )


async def ensure_wallet(session: AsyncSession, user_id: str) -> WalletOut:
    result = await session.scalars(select(Wallet).where(Wallet.user_id == user_id))
    w = result.first()
    if not w:
        w = Wallet(user_id=user_id, balance=0, currency="CNY", frozen=0)
        session.add(w)
        await session.commit()
        await session.refresh(w)
    return _wallet_model_to_out(w)


async def get_wallet_by_user_id(session: AsyncSession, user_id: str) -> WalletOut:
    result = await session.scalars(select(Wallet).where(Wallet.user_id == user_id))
    w = result.first()
    return _wallet_model_to_out(w) if w else await ensure_wallet(session, user_id)


async def change_balance(
    session: AsyncSession,
    *,
    user_id: str,
    delta: float,
    tx_type: TransactionType,
    ref_job_id: str | None = None,
    description: str | None = None,
) -> tuple[WalletOut, WalletTxOut]:
    result = await session.scalars(select(Wallet).where(Wallet.user_id == user_id))
    w = result.first()
    if not w:
        w = Wallet(user_id=user_id, balance=0, currency="CNY", frozen=0)
        session.add(w)
        await session.commit()
        await session.refresh(w)
    new_balance = float(w.balance or 0) + float(delta)
    if new_balance < 0:
        new_balance = 0.0
    w.balance = new_balance
    t = WalletTransaction(
        id=f"tx_{int(await session.scalar(select(func.count()).select_from(WalletTransaction)) or 0) + 1}",
        user_id=user_id,
        amount=abs(float(delta)),
        type=WalletTxTypeDB(tx_type.value if isinstance(tx_type, WalletTxTypeDB) else tx_type.value),
        status=WalletTxStatusDB.COMPLETED,
        ref_job_id=ref_job_id,
        description=description,
        meta={},
    )
    session.add(t)
    await session.commit()
    await session.refresh(w)
    await session.refresh(t)
    return _wallet_model_to_out(w), _tx_model_to_out(t)


async def list_wallet_txs(session: AsyncSession, user_id: str, *, offset: int = 0, limit: int | None = None) -> list[WalletTxOut]:
    stmt = select(WalletTransaction).where(WalletTransaction.user_id == user_id).order_by(WalletTransaction.created_at.desc())
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    return [_tx_model_to_out(x) for x in result]


# Preferences helpers
def _pref_model_to_out(p: UserPreferences) -> PreferencesOut:
    return PreferencesOut(
        owner_id=p.user_id,
        theme=p.theme,
        language=p.language,
        notifications=p.notifications,
        updated_at=(p.updated_at.replace(tzinfo=None) if p.updated_at else p.created_at.replace(tzinfo=None)),
        meta=p.meta or {},
    )


async def get_preferences(session: AsyncSession, user_id: str) -> PreferencesOut:
    result = await session.scalars(select(UserPreferences).where(UserPreferences.user_id == user_id))
    p = result.first()
    if not p:
        p = UserPreferences(user_id=user_id)
        session.add(p)
        await session.commit()
        await session.refresh(p)
    return _pref_model_to_out(p)


async def update_preferences(
    session: AsyncSession,
    *,
    user_id: str,
    theme: str,
    language: str,
    notifications: bool,
    meta: dict | None = None,
) -> PreferencesOut:
    result = await session.scalars(select(UserPreferences).where(UserPreferences.user_id == user_id))
    p = result.first()
    if not p:
        p = UserPreferences(user_id=user_id)
        session.add(p)
    p.theme = theme
    p.language = language
    p.notifications = notifications
    if meta is not None:
        p.meta = meta
    await session.commit()
    await session.refresh(p)
    return _pref_model_to_out(p)


# Admin: users
async def list_users_db(session: AsyncSession, *, offset: int = 0, limit: int | None = None) -> list[UserOut]:
    stmt = select(User).order_by(User.created_at.desc())
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    return [user_model_to_out(u) for u in result]


async def update_user_role(session: AsyncSession, *, user_id: str, role: str) -> UserOut | None:
    user = await session.get(User, user_id)
    if not user:
        return None
    user.role = role
    await session.commit()
    await session.refresh(user)
    return user_model_to_out(user)


async def delete_user_db(session: AsyncSession, *, user_id: str) -> bool:
    user = await session.get(User, user_id)
    if not user:
        return False
    await session.delete(user)
    await session.commit()
    return True


async def update_user_fields(session: AsyncSession, *, user_id: str, email: str | None = None, username: str | None = None) -> UserOut | None:
    user = await session.get(User, user_id)
    if not user:
        return None
    if email is not None:
        user.email = email.lower()
    if username is not None:
        user.username = username
    await session.commit()
    await session.refresh(user)
    return user_model_to_out(user)


async def update_user_password(session: AsyncSession, *, user_id: str, password_hash: str) -> UserOut | None:
    user = await session.get(User, user_id)
    if not user:
        return None
    user.password_hash = password_hash
    await session.commit()
    await session.refresh(user)
    return user_model_to_out(user)


# Admin: wallets
async def list_wallets_db(session: AsyncSession, *, offset: int = 0, limit: int | None = None) -> list[WalletOut]:
    result = await session.scalars(select(Wallet).order_by(Wallet.updated_at.desc().nullslast()))
    items = list(result)
    if offset:
        items = items[offset:]
    if limit is not None:
        items = items[:limit]
    return [_wallet_model_to_out(w) for w in items]


async def list_wallets_filtered(
    session: AsyncSession,
    *,
    currency: str | None = None,
    balance_min: float | None = None,
    balance_max: float | None = None,
    updated_after: dt.datetime | None = None,
    offset: int = 0,
    limit: int | None = None,
) -> list[WalletOut]:
    stmt = select(Wallet)
    if currency:
        stmt = stmt.where(Wallet.currency == currency)
    if balance_min is not None:
        stmt = stmt.where(Wallet.balance >= balance_min)
    if balance_max is not None:
        stmt = stmt.where(Wallet.balance <= balance_max)
    if updated_after is not None:
        stmt = stmt.where(Wallet.updated_at >= updated_after)
    stmt = stmt.order_by(Wallet.updated_at.desc().nullslast())
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    return [_wallet_model_to_out(w) for w in result]


# Admin: assets
async def update_asset_fields(session: AsyncSession, asset_id: str, **fields) -> AssetOut | None:
    asset = await session.get(Asset, asset_id)
    if not asset:
        return None
    for k, v in fields.items():
        setattr(asset, k, v)
    await session.commit()
    await session.refresh(asset)
    return asset_model_to_out(asset)


# Admin: providers create/delete
async def add_provider_db(
    session: AsyncSession,
    *,
    name: str,
    display_name: str,
    models: list[str],
    capabilities: list[str],
    enabled: bool = True,
    notes: str | None = None,
    base_url: str | None = None,
) -> ProviderInfo:
    p = Provider(
        name=name,
        display_name=display_name,
        models=models,
        capabilities=capabilities,
        enabled=enabled,
        notes=notes,
        base_url=base_url,
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return provider_model_to_info(p)


async def delete_provider_db(session: AsyncSession, *, name: str) -> bool:
    p = await session.get(Provider, name)
    if not p:
        return False
    await session.delete(p)
    await session.commit()
    return True
