from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form
from app.deps.auth import get_current_user_optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas import JobCreate, JobKind, JobOut, JobParams, JobStatus
from app.api.utils import api_error
from app.services.persistence import get_job_db, list_assets_db, next_job_id, persist_job
from app.services.store import MemoryStore, get_store
from app.services.generation import simulate_generation
from app.services.taskqueue import get_task_queue


router = APIRouter()


def _normalize_model(name: str | None) -> str:
    try:
        return (name or "").strip()
    except Exception:
        return name or ""


def _status_to_external(s: JobStatus) -> str:
    if s == JobStatus.QUEUED:
        return "queued"
    if s == JobStatus.RUNNING:
        return "processing"
    if s == JobStatus.COMPLETED:
        return "completed"
    if s == JobStatus.FAILED:
        return "failed"
    if s == JobStatus.CANCELED:
        return "failed"
    return s.value

@router.post("/images", status_code=status.HTTP_202_ACCEPTED)
async def create_image(payload: dict, store: MemoryStore = Depends(get_store), session: AsyncSession = Depends(get_session), x_api_key: str | None = Header(None)) -> dict:
    from app.config import get_settings
    settings = get_settings()
    if settings.public_api_key and x_api_key != settings.public_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("invalid api key"))
    model = _normalize_model(payload.get("model"))
    prompt = payload.get("prompt")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Prompt cannot be empty"))
    if not model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Model is required"))
    if "edit" in model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("image-edit 模型不允许用于文生图，请使用 /v1/images/edits"))
    internal_model = model or "gpt-image-1"
    kind = JobKind.TEXT_TO_IMAGE
    params = JobParams(extras={})

    try:
        new_job_id = await next_job_id(session)
    except Exception:
        new_job_id = None
    job = store.create_job(JobCreate(prompt=prompt, kind=kind, model=internal_model, provider="openai", is_public=True, params=params, source_image_name=None, owner_id=None), job_id=new_job_id)
    await persist_job(session, job)

    tq = get_task_queue()
    await tq.enqueue(job.id)

    now = dt.datetime.utcnow().isoformat() + "Z"
    return {
        "image_id": job.id,
        "task_id": None,
        "status": "queued",
        "progress": float(job.progress),
        "model": model,
        "prompt": prompt,
        "result_url": None,
        "image_url": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }


@router.post("/images/edits", status_code=status.HTTP_202_ACCEPTED)
async def edit_image(payload: dict, store: MemoryStore = Depends(get_store), session: AsyncSession = Depends(get_session), x_api_key: str | None = Header(None), current_user = Depends(get_current_user_optional)) -> dict:
    from app.config import get_settings
    settings = get_settings()
    if settings.public_api_key and x_api_key != settings.public_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("invalid api key"))
    model = _normalize_model(payload.get("model"))
    prompt = payload.get("prompt")
    image = payload.get("image")
    images = payload.get("images")
    size = payload.get("size")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Prompt cannot be empty"))
    if not model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Model is required"))
    urls: list[str] | None = None
    if images is not None:
        if not isinstance(images, list) or not images:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Images must be a non-empty list"))
        for u in images:
            if not isinstance(u, str) or not (u.startswith("http://") or u.startswith("https://")):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("All image URLs must be http/https"))
        urls = images
    else:
        if not image or not isinstance(image, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Image URL is required"))
        if not (image.startswith("http://") or image.startswith("https://")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("Image URL must be http/https"))
        urls = [image]
    normalized_model = model
    normalized_lower = normalized_model.lower()
    kind = JobKind.TEXT_TO_IMAGE
    extras = {"source_image_urls": urls} if urls and len(urls) > 1 else {"source_image_url": urls[0]}
    params = JobParams(size=size, extras=extras)

    provider = "openai"
    internal_model = normalized_model or "gpt-image-1-edit"
    if "sora" in normalized_lower:
        provider = "sora"
        internal_model = normalized_model or "sora-image"
    elif ("nano" in normalized_lower) or ("gemini" in normalized_lower):
        provider = "nano-banana-2"
        internal_model = normalized_model or "gemini-3-pro-image-preview"
    elif ("gpt-image" in normalized_lower) or ("dall-e" in normalized_lower) or ("openai" in normalized_lower):
        internal_model = normalized_model or "gpt-image-1-edit"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=api_error("不支持的图像编辑模型"))

    try:
        new_job_id = await next_job_id(session)
    except Exception:
        new_job_id = None
    job = store.create_job(JobCreate(prompt=prompt, kind=kind, model=internal_model, provider=provider, is_public=True, params=params, source_image_name=None, owner_id=(current_user.id if current_user else None)), job_id=new_job_id)
    await persist_job(session, job)

    tq = get_task_queue()
    await tq.enqueue(job.id)

    # Deduct balance if user present and price > 0
    charged = 0.0
    try:
        if current_user:
            from app.services.store import get_store as _get_store
            from app.services.persistence import get_wallet_by_user_id, change_balance
            from app.schemas import TransactionType
            store2 = _get_store()
            prices = store2.get_prices()
            price = float(prices.get("image_to_image", prices.get("text_to_image", 0.0)))
            if price > 0:
                wallet = await get_wallet_by_user_id(session, current_user.id)
                if wallet.balance < price:
                    raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=api_error("Insufficient balance"))
                await change_balance(session, user_id=current_user.id, delta=-price, tx_type=TransactionType.DEDUCT, ref_job_id=job.id, description="image_to_image")
                charged = price
    except HTTPException:
        raise
    except Exception:
        pass

    now = dt.datetime.utcnow().isoformat() + "Z"
    return {
        "image_id": job.id,
        "task_id": None,
        "status": "queued",
        "progress": float(job.progress),
        "model": model,
        "prompt": prompt,
        "result_url": None,
        "image_url": None,
        "error_message": None,
        "price_charged": charged,
        "created_at": now,
        "updated_at": now,
    }


@router.post("/uploads/external")
async def upload_external_image(
    file: UploadFile = File(...),
    filename: str | None = Form(None),
    x_api_key: str | None = Header(None),
) -> dict:
    from app.config import get_settings
    settings = get_settings()
    if settings.public_api_key and x_api_key != settings.public_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("invalid api key"))
    base = settings.ext_image_upload_base
    if not base:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=api_error("external upload not configured"))
    import time, uuid
    mime = (file.content_type or "").lower()
    ext = "jpg"
    if "jpeg" in mime:
        ext = "jpg"
    elif "png" in mime:
        ext = "png"
    elif "bmp" in mime:
        ext = "bmp"
    elif "tiff" in mime:
        ext = "tiff"
    elif "webp" in mime:
        ext = "webp"
    name = filename or (file.filename or f"ls-{int(time.time())}-{uuid.uuid4().hex[:8]}.{ext}")
    if "." not in name:
        name = f"{name}.{ext}"
    data = await file.read()
    import requests
    files = {
        "image": (name, data, file.content_type or "application/octet-stream"),
    }
    try:
        resp = requests.post(base, files=files, timeout=60)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=api_error(f"upload failed: {exc}"))
    if not resp.ok:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=api_error(f"upload failed: {resp.status_code}"))
    try:
        j = resp.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=api_error("invalid upload response"))
    url = j.get("url")
    success = bool(j.get("success"))
    if not success or not isinstance(url, str):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=api_error("upload service error"))
    return {"url": url}


@router.get("/images/{image_id}")
async def get_image(image_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    job = await get_job_db(session, image_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Not found"))
    result_url = None
    if job.asset_id:
        assets = await list_assets_db(session)
        for a in assets:
            if a.id == job.asset_id:
                result_url = a.url
                break
    return {
        "image_id": job.id,
        "task_id": None,
        "status": _status_to_external(job.status),
        "progress": float(job.progress),
        "model": job.model,
        "prompt": job.prompt,
        "result_url": result_url,
        "image_url": result_url,
        "error_message": job.error,
        "created_at": job.created_at.isoformat() + "Z",
        "updated_at": job.updated_at.isoformat() + "Z",
    }