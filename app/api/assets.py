from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import UploadFile, File, Form

from app.deps.auth import get_current_user_optional, get_current_user
from app.db import get_session
from app.schemas import AssetList, AssetOut, AssetType, UserOut
from app.services.persistence import delete_asset_db, list_assets_db, update_asset_fields
from app.services.storage import delete_asset_files
from app.services.storage import ensure_storage_dir
from app.config import get_settings
from pathlib import Path
from app.services.store import MemoryStore, get_store
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

router = APIRouter()


@router.get("", response_model=AssetList)
async def list_assets(
    *,
    store: MemoryStore = Depends(get_store),
    type: AssetType | None = Query(None, description="Filter by type"),
    provider: str | None = Query(None, description="Filter by provider"),
    public: bool | None = Query(None, description="Filter by public flag"),
    owner_only: bool | None = Query(None, description="Only show current user's assets"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserOut | None = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> AssetList:
    offset = (max(1, page) - 1) * max(1, min(100, limit))
    items = await list_assets_db(session, asset_type=type, provider=provider, public_only=public, offset=offset, limit=limit)
    if current_user is None:
        items = [a for a in items if a.is_public]
    elif not _is_admin(current_user):
        items = [a for a in items if a.is_public or a.owner_id == current_user.id]
    if owner_only:
        if current_user is None:
            items = []
        else:
            items = [a for a in items if a.owner_id == current_user.id]
    total = len(items)
    try:
        from app.services.persistence import count_assets_db
        total_all = await count_assets_db(session)
    except Exception:
        total_all = None
    return AssetList(items=items, total=total, total_all=total_all)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: str,
    store: MemoryStore = Depends(get_store),
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    assets_db = await list_assets_db(session)
    asset = next((a for a in assets_db if a.id == asset_id), None)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Asset not found"))
    if not _is_admin(current_user) and (current_user is None or asset.owner_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Unauthorized"))
    delete_asset_files(asset)
    store.delete_asset(asset_id)
    await delete_asset_db(session, asset_id)
    try:
        from app.services.audit import write as audit_write
        audit_write("asset.delete", {"asset_id": asset_id, "user_id": current_user.id})
    except Exception:
        pass


def _is_admin(user: UserOut | None) -> bool:
    return bool(user and user.role == "admin")


@router.post("/upload", response_model=AssetOut)
async def upload_asset(
    *,
    file: UploadFile = File(...),
    public: bool = Form(True),
    provider: str | None = Form(None),
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AssetOut:
    settings = get_settings()
    base = Path(settings.storage_base)
    ensure_storage_dir(base)
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Empty file"))
    ct = file.content_type or ""
    if ct.startswith("image/"):
        kind = AssetType.IMAGE
        ext = ".png"
    elif ct.startswith("video/"):
        kind = AssetType.VIDEO
        ext = ".mp4"
    elif ct.startswith("audio/"):
        kind = AssetType.AUDIO
        ext = ".mp3"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Unsupported content type"))
    # persist file
    from app.models.asset import Asset as AssetModel
    asset_id = f"asset_{int(await session.scalar(select(func.count()).select_from(AssetModel)) or 0) + 1}"
    rel = f"uploads/{asset_id}{ext}"
    dest = base / rel
    ensure_storage_dir(dest.parent)
    with dest.open("wb") as f:
        f.write(data)
    url = f"/media/{rel}"
    # build meta minimally
    meta = {"filename": file.filename, "content_type": ct}
    # add DB record
    from app.models.asset import AssetTypeDB, Asset as AssetModel
    asset = AssetModel(
        id=asset_id,
        owner_id=current_user.id,
        type=AssetTypeDB(kind.value),
        provider=provider,
        url=url,
        preview_url=url,
        meta=meta,
        is_public=public,
    )
    session.add(asset)
    await session.commit()
    return AssetOut(
        id=asset_id,
        type=kind,
        provider=provider,
        url=url,
        preview_url=url,
        meta=meta,
        is_public=public,
        created_at=asset.created_at.replace(tzinfo=None),
        owner_id=current_user.id,
    )
from app.api.utils import api_error
@router.patch("/{asset_id}", response_model=AssetOut)
async def patch_asset(
    asset_id: str,
    public: bool,
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AssetOut:
    assets_db = await list_assets_db(session)
    asset = next((a for a in assets_db if a.id == asset_id), None)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Asset not found"))
    if not _is_admin(current_user) and (current_user is None or asset.owner_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Unauthorized"))
    updated = await update_asset_fields(session, asset_id, is_public=public)
    return updated
