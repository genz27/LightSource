from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from starlette.responses import JSONResponse
import datetime as dt
from app.api.utils import api_error

from app.deps.auth import get_current_user_optional, get_current_user
from app.db import get_session
from app.schemas import (
    JobCreate,
    JobKind,
    JobList,
    JobOut,
    JobParams,
    JobStatusOut,
    JobStatus,
    Orientation,
    UserOut,
)
from app.services.generation import simulate_generation
from app.services.persistence import change_balance, get_wallet_by_user_id
from app.schemas import TransactionType
from app.services.persistence import (
    get_job_db,
    list_jobs_db,
    next_job_id,
    persist_job,
    update_job_fields,
)
from app.services.store import MemoryStore, get_store
from app.services.storage import save_source_image
from app.services.taskqueue import get_task_queue
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from typing import List

router = APIRouter()


def _is_admin(user: UserOut | None) -> bool:
    return bool(user and user.role == "admin")


@router.get("", response_model=JobList)
async def list_jobs(
    store: MemoryStore = Depends(get_store),
    current_user=Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
    page: int = 1,
    limit: int = 20,
) -> JobList:
    page = max(1, page)
    limit = max(1, min(100, limit))
    offset = (page - 1) * limit
    items = await list_jobs_db(session, offset=offset, limit=limit)
    if current_user is None:
        items = [j for j in items if j.is_public]
    elif _is_admin(current_user):
        # Admin can view all jobs.
        pass
    else:
        items = [j for j in items if j.is_public or j.owner_id == current_user.id]
    total = len(items)
    try:
        from app.services.persistence import count_jobs_db
        total_all = await count_jobs_db(session)
    except Exception:
        total_all = None
    return JobList(items=items, total=total, total_all=total_all)


@router.get("/active", response_model=List[JobStatusOut])
async def get_active_jobs(
    limit: int = 20,
    owner_only: bool | None = None,
    store: MemoryStore = Depends(get_store),
    current_user=Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> List[JobStatusOut]:
    items = await list_jobs_db(session)
    def _visible(j: JobOut) -> bool:
        if j.status not in {JobStatus.RUNNING, JobStatus.QUEUED}:
            return False
        if j.is_public:
            return True
        if _is_admin(current_user):
            return True
        if current_user and j.owner_id == current_user.id:
            return True
        return False
    if owner_only and current_user:
        items = [j for j in items if j.owner_id == current_user.id]
    items = [j for j in items if _visible(j)]
    items = items[: max(0, min(100, limit))]
    return [
        JobStatusOut(
            id=j.id,
            status=j.status,
            progress=j.progress,
            asset_id=j.asset_id,
            error=j.error,
            updated_at=j.updated_at,
        )
        for j in items
    ]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: str,
    store: MemoryStore = Depends(get_store),
    current_user=Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> JobOut:
    job = await get_job_db(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Job not found"))
    if not job.is_public and not _is_admin(current_user) and (
        current_user is None or job.owner_id != current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=api_error("Unauthorized"))
    return job


@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    store: MemoryStore = Depends(get_store),
    current_user=Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
    debug: bool | None = None,
    ) -> dict:
    if debug is None:
        try:
            debug = bool(getattr(store, "debug_enabled", False)) or bool(getattr(get_settings(), "debug", False))
        except Exception:
            debug = False
    job = await get_job_db(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not job.is_public and not _is_admin(current_user) and (
        current_user is None or job.owner_id != current_user.id
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    mem_job = store.get_job(job_id)
    try:
        runtime_job = mem_job if (mem_job and (mem_job.updated_at >= job.updated_at)) else job
        if mem_job and (job.updated_at > mem_job.updated_at or job.status != mem_job.status or job.progress != mem_job.progress):
            try:
                store.update_job(job.id, status=job.status, progress=job.progress, asset_id=job.asset_id, error=job.error, params=job.params)
            except Exception:
                pass
    except Exception:
        runtime_job = mem_job or job
    extras = getattr(job.params, "extras", {}) or {}
    error_detail = extras.get("error_detail")
    provider_resp_existing = extras.get("provider_response") or {}
    provider_raw_existing = provider_resp_existing.get("raw") or {}
    vendor_video_id = provider_raw_existing.get("video_id") or None
    provider_status = None
    provider_progress = None
    provider_task_id = None
    provider_result_url = None
    provider_model_name = None
    provider_created_at = None
    provider_updated_at = None
    provider_error_message = None
    provider_detail: dict | None = None
    def _norm_progress(val) -> int | None:
        try:
            if isinstance(val, (int, float)):
                if 0 <= float(val) <= 1:
                    return int(float(val) * 100)
                return int(float(val))
            if isinstance(val, str):
                f = float(val)
                if 0 <= f <= 1:
                    return int(f * 100)
                return int(f)
        except Exception:
            return None
        return None

    if job.kind in {JobKind.TEXT_TO_VIDEO, JobKind.IMAGE_TO_VIDEO}:
        try:
            from app.services.persistence import get_provider_by_name
            p = await get_provider_by_name(session, job.provider) if job.provider else None
            if p and p.enabled and isinstance(vendor_video_id, str) and vendor_video_id:
                from app.interface.sora2 import get_video
                base_eff = p.base_url
                try:
                    b = str(base_eff or "").lower()
                    if (not base_eff) or ("sora2.example" in b) or b.endswith(".example"):
                        base_eff = None
                except Exception:
                    base_eff = None
                provider_detail = get_video(vendor_video_id, api_key=p.api_token, base_url=base_eff, debug=bool(debug))
                if isinstance(provider_detail, dict) and not provider_detail.get("error"):
                    raw_status = provider_detail.get("status")
                    # normalize common provider status names
                    status_map = {
                        "succeeded": "completed",
                        "completed": "completed",
                        "processing": "processing",
                        "running": "processing",
                        "queued": "queued",
                        "pending": "queued",
                        "failed": "failed",
                        "error": "failed",
                    }
                    provider_status = status_map.get(str(raw_status).lower(), str(raw_status).lower() if isinstance(raw_status, str) else None)
                    provider_progress = _norm_progress(provider_detail.get("progress"))
                    if provider_status == "completed" and provider_progress is None:
                        provider_progress = 100
                    provider_task_id = provider_detail.get("task_id")
                    provider_result_url = provider_detail.get("video_url") or provider_detail.get("result_url")
                    provider_model_name = provider_detail.get("model")
                    provider_created_at = provider_detail.get("created_at")
                    provider_updated_at = provider_detail.get("updated_at")
                elif isinstance(provider_detail, dict):
                    err = provider_detail.get("error") or {}
                    provider_error_message = err.get("message") or provider_detail.get("detail")
                    msg = (provider_error_message or "").lower()
                    code = err.get("code")
                    if ("not found" in msg) or (code in (404, 410)):
                        provider_status = "failed"
                        status_ext = "failed"
                        try:
                            store.update_job(job.id, status=JobStatus.FAILED)
                            await update_job_fields(session, job.id, status=JobStatus.FAILED)
                        except Exception:
                            pass
        except Exception:
            pass
    status_ext = (
        "queued" if runtime_job.status == JobStatus.QUEUED else
        ("processing" if runtime_job.status == JobStatus.RUNNING else
         ("completed" if runtime_job.status == JobStatus.COMPLETED else
          ("failed" if runtime_job.status in {JobStatus.FAILED, JobStatus.CANCELED} else runtime_job.status.value)))
    )
    if isinstance(provider_status, str):
        status_ext = provider_status
        try:
            if provider_status == "completed":
                store.update_job(job.id, status=JobStatus.COMPLETED, progress=100)
                await update_job_fields(session, job.id, status=JobStatus.COMPLETED, progress=100)
            elif provider_status == "processing":
                pr = provider_progress if isinstance(provider_progress, (int, float)) else None
                if pr is None:
                    pr = runtime_job.progress if isinstance(runtime_job.progress, (int, float)) else None
                if pr is None:
                    pr = 1
                store.update_job(job.id, status=JobStatus.RUNNING, progress=int(pr))
                await update_job_fields(session, job.id, status=JobStatus.RUNNING, progress=int(pr))
            elif provider_status == "queued":
                store.update_job(job.id, status=JobStatus.QUEUED)
                await update_job_fields(session, job.id, status=JobStatus.QUEUED)
            elif provider_status == "failed":
                store.update_job(job.id, status=JobStatus.FAILED)
                await update_job_fields(session, job.id, status=JobStatus.FAILED)
            elif provider_status == "succeeded":
                store.update_job(job.id, status=JobStatus.COMPLETED, progress=100)
                await update_job_fields(session, job.id, status=JobStatus.COMPLETED, progress=100)
        except Exception:
            pass
    fallback_progress = None
    try:
        from app.services.metrics import metrics
        start = metrics.started_at.get(job.id)
        if start:
            elapsed = (dt.datetime.utcnow() - start).total_seconds()
            steps = [5, 15, 30, 50, 70, 85, 95]
            idx = int(elapsed / 1.2)
            if idx < 0:
                idx = 0
            if idx >= len(steps):
                idx = len(steps) - 1
            fallback_progress = steps[idx]
            if status_ext == "queued" and fallback_progress:
                status_ext = "processing"
    except Exception:
        pass
    result_url = None
    if job.asset_id:
        from app.services.persistence import list_assets_db
        assets = await list_assets_db(session)
        for a in assets:
            if a.id == job.asset_id:
                result_url = a.url
                break
    if provider_result_url:
        result_url = provider_result_url
        try:
            if (job.kind in {JobKind.TEXT_TO_VIDEO, JobKind.IMAGE_TO_VIDEO}) and provider_status == "completed" and not job.asset_id and isinstance(provider_result_url, str):
                frames = 20
                duration_seconds = 6
                resolution_meta = job.params.size or ("1024x576" if (job.params.orientation or "landscape") == "landscape" else "576x1024")
                provider_response_meta = {
                    "provider": job.provider,
                    "model": provider_model_name or job.model,
                    "status": provider_status,
                    "orientation": (job.params.orientation.value if job.params.orientation else None),
                    "resolution": resolution_meta,
                    "raw": {
                        "status": provider_status,
                        "progress": provider_progress,
                        "video_url": provider_result_url,
                        "model": provider_model_name,
                        "task_id": provider_task_id,
                    },
                }
                asset_meta = {
                    "model": provider_model_name or job.model,
                    "orientation": (job.params.orientation.value if job.params.orientation else None),
                    "size": resolution_meta,
                    "frames": frames,
                    "duration_seconds": duration_seconds,
                    "provider_response": provider_response_meta,
                }
                asset = store.create_asset(
                    kind=job.kind,
                    provider=job.provider,
                    is_public=job.is_public,
                    meta=asset_meta,
                    url=provider_result_url,
                    owner_id=job.owner_id,
                )
                from app.services.persistence import persist_asset
                await persist_asset(
                    session,
                    asset_id=asset.id,
                    owner_id=job.owner_id,
                    kind=job.kind.value,
                    provider=job.provider,
                    is_public=job.is_public,
                    meta=asset.meta,
                    url=asset.url,
                    preview_url=asset.preview_url,
                )
                await update_job_fields(session, job.id, asset_id=asset.id)
                job = await get_job_db(session, job.id) or job
                result_url = asset.url
        except Exception:
            pass
    provider_resp = extras.get("provider_response") or {}
    raw = provider_resp.get("raw") or {}
    task_id = provider_task_id or provider_resp.get("task_id") or raw.get("task_id")
    if job.kind in {JobKind.TEXT_TO_VIDEO, JobKind.IMAGE_TO_VIDEO}:
        orientation = getattr(job.params, "orientation", None)
        if orientation:
            model_name = f"sora-video-{orientation.value}"
        else:
            model_name = job.model
        if provider_model_name:
            model_name = provider_model_name
        payload = {
            "video_id": vendor_video_id or job.id,
            "task_id": task_id,
            "status": status_ext,
            "progress": float(provider_progress if isinstance(provider_progress, (int, float)) else (runtime_job.progress or fallback_progress or 0)),
            "model": model_name,
            "prompt": job.prompt,
            "image_provided": bool(extras.get("source_image_url")),
            "result_url": result_url,
            "video_url": result_url,
            "error_message": error_detail or provider_error_message or job.error,
            "created_at": provider_created_at or (job.created_at.isoformat() + "Z"),
            "updated_at": provider_updated_at or (job.updated_at.isoformat() + "Z"),
        }
        if debug:
            if isinstance(provider_detail, dict) and provider_detail.get("debug"):
                payload["provider_debug"] = provider_detail.get("debug")
            elif isinstance(raw, dict) and raw.get("debug"):
                payload["provider_debug"] = raw.get("debug")
        return JSONResponse(content=payload, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
    else:
        payload = {
            "image_id": job.id,
            "task_id": task_id,
            "status": status_ext,
            "progress": float(provider_progress if isinstance(provider_progress, (int, float)) else (runtime_job.progress or fallback_progress or 0)),
            "model": job.model,
            "prompt": job.prompt,
            "result_url": result_url,
            "image_url": result_url,
            "error_message": error_detail or job.error,
            "error_detail": error_detail,
            "created_at": job.created_at.isoformat() + "Z",
            "updated_at": job.updated_at.isoformat() + "Z",
        }
        return JSONResponse(content=payload, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@router.get("/status", response_model=List[JobStatusOut])
async def get_jobs_status(
    ids: str,
    store: MemoryStore = Depends(get_store),
    current_user=Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_session),
) -> List[JobStatusOut]:
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    results: List[JobStatusOut] = []
    for job_id in id_list:
        job = await get_job_db(session, job_id)
        if not job:
            continue
        if not job.is_public and not _is_admin(current_user) and (
            current_user is None or job.owner_id != current_user.id
        ):
            continue
        results.append(
            JobStatusOut(
                id=job.id,
                status=job.status,
                progress=job.progress,
                asset_id=job.asset_id,
                error=getattr(job.params, "extras", {}).get("error_detail") or job.error,
                updated_at=job.updated_at,
            )
        )
    return JSONResponse(content=[r.dict() for r in results], headers={"Cache-Control": "no-store, no-cache, must-revalidate"})




@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    *,
    prompt: Annotated[str, Form(...)],
    kind: Annotated[JobKind, Form(...)],
    model: Annotated[str | None, Form()] = None,
    provider: Annotated[str | None, Form()] = None,
    is_public: Annotated[bool, Form()] = True,
    orientation: Annotated[Orientation | None, Form()] = None,
    size: Annotated[str | None, Form()] = None,
    seed: Annotated[int | None, Form()] = None,
    style: Annotated[str | None, Form()] = None,
    guidance: Annotated[float | None, Form()] = None,
    source_image: Annotated[UploadFile | None, File()] = None,
    store: MemoryStore = Depends(get_store),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> JobOut:
    if kind == JobKind.IMAGE_TO_VIDEO and source_image is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source image required for image_to_video")
    _validate_model_kind(kind, model)
    _validate_required_orientation(kind, orientation)
    _validate_guidance(guidance)

    params = JobParams(
        orientation=orientation,
        size=size,
        seed=seed,
        style=style,
        guidance=guidance,
        extras={},
    )
    if current_user:
        try:
            from app.services.store import get_store
            store = get_store()
            prices = store.get_prices()
            key = kind.value if hasattr(kind, "value") else str(kind)
            price = float(prices.get(key, 0.0))
        except Exception:
            price = 0.0
        if price > 0:
            wallet = await get_wallet_by_user_id(session, current_user.id)
            if wallet.balance < price:
                raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=api_error("Insufficient balance"))
    try:
        new_job_id = await next_job_id(session)
    except Exception:
        new_job_id = None

    job = store.create_job(
        JobCreate(
            prompt=prompt,
            kind=kind,
            model=model,
            provider=provider or _infer_provider(model),
            is_public=is_public,
            params=params,
            source_image_name=None,
            owner_id=current_user.id if current_user else None,
        ),
        job_id=new_job_id,
    )
    await persist_job(session, job)
    if current_user:
        try:
            from app.services.store import get_store
            store = get_store()
            prices = store.get_prices()
            key = job.kind.value if hasattr(job.kind, "value") else str(job.kind)
            price = float(prices.get(key, 0.0))
        except Exception:
            price = 0.0
        if price > 0:
            await change_balance(session, user_id=current_user.id, delta=-price, tx_type=TransactionType.DEDUCT, ref_job_id=job.id, description=f"{job.kind.value}")
    try:
        from app.services.audit import write as audit_write
        audit_write("job.create", {"job_id": job.id, "user_id": current_user.id if current_user else None, "kind": job.kind.value})
    except Exception:
        pass

    source_image_name = None
    if source_image:
        rel_path, url = save_source_image(job.id, source_image)
        source_image_name = rel_path
        params.extras["source_image_url"] = url
        job = store.update_job(job.id, params=params)

    # 入队，由后台 worker 执行
    tq = get_task_queue()
    await tq.enqueue(job.id)
    return job


@router.post("/{job_id}/cancel", response_model=JobOut)
async def cancel_job(
    job_id: str,
    store: MemoryStore = Depends(get_store),
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> JobOut:
    job = await get_job_db(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not _is_admin(current_user) and job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if job.status in {JobStatus.COMPLETED, JobStatus.CANCELED, JobStatus.FAILED}:
        return job
    # 更新内存状态（如果存在），以便模拟任务能感知取消
    if store.get_job(job_id):
        job = store.update_job(job_id, status=JobStatus.CANCELED, progress=0)
    await update_job_fields(session, job_id, status=JobStatus.CANCELED, progress=0)
    try:
        from app.services.audit import write as audit_write
        audit_write("job.cancel", {"job_id": job_id, "user_id": current_user.id})
    except Exception:
        pass
    
    return job


def _infer_provider(model: str | None) -> str | None:
    if not model:
        return None
    m = model.lower()
    if "sora-image" in m:
        return "sora"
    if "sora" in m:
        return "sora2"
    if "nano" in m or "gemini-3-pro-image-preview" in m or "gemini-2.5-flash-image" in m:
        return "nano-banana-2"
    if "qwen" in m:
        return "qwen"
    if "flux" in m or "musepublic" in m:
        return "flux"
    if "majicflus" in m or "mailand" in m:
        return "majicflus"
    return None


def _validate_model_kind(kind: JobKind, model: str | None) -> None:
    # Accept all model strings; provider selection is driven by channel capabilities.
    return


def _validate_required_orientation(kind: JobKind, orientation: Orientation | None) -> None:
    if kind in {JobKind.TEXT_TO_VIDEO, JobKind.IMAGE_TO_VIDEO} and orientation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="orientation is required for video kinds",
        )


def _validate_guidance(guidance: float | None) -> None:
    if guidance is None:
        return
    if guidance < 0 or guidance > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="guidance must be between 0 and 20",
        )
