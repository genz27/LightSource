from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas import JobCreate, JobKind, JobOut, JobParams, JobStatus, Orientation
from app.services.persistence import get_job_db, list_assets_db, next_job_id, persist_job
from app.services.store import MemoryStore, get_store
from app.services.generation import simulate_generation
from app.api.utils import api_error
from app.services.taskqueue import get_task_queue


router = APIRouter()


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


def _error(message: str) -> dict:
    return api_error(message)


def _infer_orientation(model: str | None) -> Optional[Orientation]:
    if not model:
        return None
    m = model.lower()
    if "landscape" in m:
        return Orientation.LANDSCAPE
    if "portrait" in m:
        return Orientation.PORTRAIT
    return None


@router.post("/videos", status_code=status.HTTP_202_ACCEPTED)
async def create_video(
    payload: dict,
    store: MemoryStore = Depends(get_store),
    session: AsyncSession = Depends(get_session),
    x_api_key: str | None = Header(None),
) -> dict:
    from app.config import get_settings
    settings = get_settings()
    if settings.public_api_key and x_api_key != settings.public_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_error("invalid api key"))
    model = payload.get("model")
    prompt = payload.get("prompt")
    image = payload.get("image")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_error("Prompt cannot be empty"))
    if not model or not isinstance(model, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_error("Model is required"))

    orientation = _infer_orientation(model) or Orientation.LANDSCAPE
    kind = JobKind.IMAGE_TO_VIDEO if image else JobKind.TEXT_TO_VIDEO
    internal_model = "sora2-video"
    params = JobParams(orientation=orientation, extras={})
    if image:
        params.extras["source_image_url"] = image

    try:
        new_job_id = await next_job_id(session)
    except Exception:
        new_job_id = None
    job = store.create_job(
        JobCreate(
            prompt=prompt,
            kind=kind,
            model=internal_model,
            provider="sora2",
            is_public=True,
            params=params,
            source_image_name=None,
            owner_id=None,
        ),
        job_id=new_job_id,
    )
    await persist_job(session, job)

    tq = get_task_queue()
    await tq.enqueue(job.id)

    now = dt.datetime.utcnow().isoformat() + "Z"
    return {
        "video_id": job.id,
        "task_id": None,
        "status": _status_to_external(job.status),
        "progress": float(job.progress),
        "model": model,
        "prompt": prompt,
        "image_provided": bool(image),
        "result_url": None,
        "video_url": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }


@router.get("/videos/{video_id}")
async def get_video(video_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    job = await get_job_db(session, video_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_error("Not found"))
    result_url = None
    if job.asset_id:
        assets = await list_assets_db(session)
        for a in assets:
            if a.id == job.asset_id:
                result_url = a.url
                break
    return {
        "video_id": job.id,
        "task_id": None,
        "status": _status_to_external(job.status),
        "progress": float(job.progress),
        "model": job.model,
        "prompt": job.prompt,
        "image_provided": bool(job.params.extras.get("source_image_url")) if job.params and job.params.extras else False,
        "result_url": result_url,
        "video_url": result_url,
        "error_message": job.error,
        "created_at": job.created_at.isoformat() + "Z",
        "updated_at": job.updated_at.isoformat() + "Z",
    }