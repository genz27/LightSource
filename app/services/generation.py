from __future__ import annotations

import asyncio
import datetime as dt
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.schemas import JobKind, JobOut, JobStatus
 
from app.services.persistence import (
    persist_asset,
    update_job_fields,
    get_provider_by_name,
)
from app.services.storage import placeholder_output
from app.services.store import MemoryStore
from app.interface.registry import resolve_adapter
from app.services.metrics import metrics


async def simulate_generation(
    *, job: JobOut, store: MemoryStore, source_image_name: Optional[str] = None
) -> None:
    """Generation orchestrator for demo environment.

    - Maintains the queued -> running -> completed lifecycle with progress ticks.
    - When provider is a configured Qwen channel and kind is text_to_image,
      delegates the actual image generation to ModelScope Qwen API via
      `app.interface.qwen`, using provider.base_url + provider.api_token.
    - For other providers, falls back to a simple mocked provider_response
      and placeholder output, while keeping the Job/Asset contract stable.
    """

    # ensure session per task
    session: AsyncSession
    job = store.update_job(job.id, status=JobStatus.RUNNING, progress=1)
    async with SessionLocal() as session:
        await update_job_fields(session, job.id, status=JobStatus.RUNNING, progress=1)
    metrics.record_transition(JobStatus.QUEUED, JobStatus.RUNNING)
    metrics.mark_started(job.id)

    # If this is a Qwen text-to-image job and channel is configured,
    # kick off provider call in a background thread while we stream progress.
    qwen_task: asyncio.Task | None = None
    attempted_external = False
    async with SessionLocal() as session:
        provider = await get_provider_by_name(session, job.provider) if job.provider else None
    adapter = resolve_adapter(provider.name) if provider and provider.enabled else None
    if adapter and job.kind == JobKind.TEXT_TO_IMAGE and provider:
        attempted_external = True
        src_url = None
        try:
            src_url = job.params.extras.get("source_image_url") if job.params and job.params.extras else None
        except Exception:
            src_url = None
        src_urls = None
        try:
            src_urls = job.params.extras.get("source_image_urls") if job.params and job.params.extras else None
        except Exception:
            src_urls = None
        use_edit = bool(src_url) and ((job.model or "").startswith("qwen-image-edit") or ("edit" in (job.model or "")))
        if not use_edit and isinstance(src_urls, list) and src_urls:
            use_edit = ((job.model or "").startswith("qwen-image-edit") or ("edit" in (job.model or "")))
        if use_edit:
            qwen_task = asyncio.create_task(
                asyncio.to_thread(
                    adapter.edit_image,
                    src_urls if isinstance(src_urls, list) and src_urls else (src_url or ""),
                    job.prompt,
                    model=job.model or "qwen-image-edit",
                    api_key=provider.api_token,
                    base_url=provider.base_url or "",
                    size=job.params.size,
                )
            )
        else:
            qwen_task = asyncio.create_task(
                asyncio.to_thread(
                    adapter.generate_image,
                    job.prompt,
                    model=job.model or "qwen-image",
                    api_key=provider.api_token,
                    base_url=provider.base_url or "",
                    size=job.params.size,
                )
            )

    vendor_video_id: str | None = None
    if provider and provider.enabled and adapter and job.kind in {JobKind.TEXT_TO_VIDEO, JobKind.IMAGE_TO_VIDEO}:
        attempted_external = True
        resolution_boot = job.params.size or (
            "1024x576" if (job.params.orientation or "landscape") == "landscape" else "576x1024"
        )
        orientation_str = (job.params.orientation.value if job.params.orientation else None)
        model_to_send = (
            f"sora-video-{orientation_str}" if orientation_str in ("landscape", "portrait") else (job.model or "sora2-video")
        )
        src_url_boot = job.params.extras.get("source_image_url") if job.params and job.params.extras else None
        try:
            base_eff = provider.base_url
            if not base_eff or ("sora2.example" in str(base_eff).lower() or str(base_eff).lower().endswith(".example")):
                base_eff = None
            data_boot = adapter.create_video(
                job.prompt,
                model=model_to_send,
                image=(src_url_boot or None),
                api_key=provider.api_token,
                base_url=base_eff,
                debug=getattr(store, "debug_enabled", False),
            )
            vendor_video_id = (data_boot or {}).get("video_id")
            provider_response_boot = {
                "provider": "sora2",
                "model": model_to_send,
                "status": (data_boot or {}).get("status") or "queued",
                "orientation": orientation_str,
                "duration_seconds": 6,
                "resolution": resolution_boot,
                "raw": data_boot,
            }
            params_boot = job.params
            extras_boot = dict(getattr(params_boot, "extras", {}) or {})
            extras_boot["provider_response"] = provider_response_boot
            params_boot.extras = extras_boot
            job = store.update_job(job.id, params=params_boot)
            async with SessionLocal() as session:
                await update_job_fields(session, job.id, params=params_boot.dict() if hasattr(params_boot, "dict") else params_boot)
        except Exception:
            pass

    # Progress should feel realistic: rise gradually to 95%, then finish at 100% only when
    # the provider task (if any) has completed and the asset has been written.
    steps = [5, 15, 30, 50, 70, 85, 95]
    try:
        for progress in steps:
            await asyncio.sleep(1.2)
            # respect external cancel
            current = store.get_job(job.id)
            if current and current.status == JobStatus.CANCELED:
                metrics.record_transition(JobStatus.RUNNING, JobStatus.CANCELED)
                metrics.mark_finished(job.id)
                return
            job = store.update_job(job.id, progress=progress)
            async with SessionLocal() as session:
                await update_job_fields(session, job.id, progress=progress)
        

        # If we dispatched a provider task, wait for completion and capture provider response.
        image_url: str | None = None
        provider_response: dict | None = None
        if qwen_task is not None:
            try:
                image_url, provider_response = await qwen_task
            except Exception as exc:  # pragma: no cover - external provider guard
                provider_response = {
                    "provider": "qwen",
                    "status": "failed",
                    "error": str(exc),
                }

        if provider and provider.enabled and adapter and job.kind in {JobKind.TEXT_TO_VIDEO, JobKind.IMAGE_TO_VIDEO} and vendor_video_id:
            attempted_external = True
            resolution = job.params.size or ("1024x576" if (job.params.orientation or "landscape") == "landscape" else "576x1024")
            duration_seconds = 6
            try:
                base_eff = provider.base_url
                if not base_eff or ("sora2.example" in str(base_eff).lower() or str(base_eff).lower().endswith(".example")):
                    base_eff = None
                detail = adapter.get_video(vendor_video_id, api_key=provider.api_token, base_url=base_eff, debug=getattr(store, "debug_enabled", False))
                video_url = (detail or {}).get("video_url") or (detail or {}).get("result_url")
                provider_response = {
                    "provider": "sora2",
                    "model": (detail or {}).get("model") or (job.model or "sora2-video"),
                    "status": (detail or {}).get("status") or ("succeeded" if video_url else "processing"),
                    "orientation": (job.params.orientation.value if job.params.orientation else None),
                    "duration_seconds": duration_seconds,
                    "resolution": resolution,
                    "raw": detail,
                }
                if provider_response and video_url:
                    image_url = video_url
            except Exception:
                pass

        # finish + create asset record with enriched meta and audit info
        is_image = job.kind == JobKind.TEXT_TO_IMAGE
        frames = 1 if is_image else 20
        duration_seconds = 0 if is_image else 6
        resolution = job.params.size or ("1024x1024" if is_image else ("1024x576" if (job.params.orientation or "landscape") == "landscape" else "576x1024"))
        finished_at = dt.datetime.utcnow().isoformat() + "Z"

        if provider_response is None:
            provider_response = {
                "provider": job.provider,
                "model": job.model,
                "status": "succeeded",
                "frames": frames,
                "duration_seconds": duration_seconds,
                "resolution": resolution,
                "orientation": job.params.orientation.value if job.params.orientation else None,
                "finished_at": finished_at,
            }

        params = job.params
        extras = dict(getattr(params, "extras", {}) or {})
        extras["provider_response"] = provider_response
        params.extras = extras
        job = store.update_job(job.id, params=params)
        async with SessionLocal() as session:
            await update_job_fields(session, job.id, params=params.dict() if hasattr(params, "dict") else params)

        if attempted_external and not _valid_url(image_url):
            async with SessionLocal() as session:
                await update_job_fields(session, job.id, status=JobStatus.FAILED, error=str(provider_response))
            metrics.record_transition(JobStatus.RUNNING, JobStatus.FAILED)
            metrics.mark_finished(job.id)
            store.update_job(job.id, status=JobStatus.FAILED, error=str(provider_response))
            return
        output_url = image_url if _valid_url(image_url) else placeholder_output(job.kind.value, job.id)[1]

        asset_meta = {
            "model": job.model,
            "orientation": job.params.orientation.value if job.params.orientation else None,
            "size": resolution,
            "seed": getattr(job.params, "seed", None),
            "style": job.params.style,
            "guidance": job.params.guidance,
            "source_image": source_image_name,
            "frames": frames,
            "duration_seconds": duration_seconds,
            "provider_response": provider_response,
        }

        asset = store.create_asset(
            kind=job.kind,
            provider=job.provider,
            is_public=job.is_public,
            meta=asset_meta,
            url=output_url,
            owner_id=job.owner_id,
        )
        async with SessionLocal() as session:
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
            await update_job_fields(
                session,
                job.id,
                status=JobStatus.COMPLETED,
                progress=100,
                asset_id=asset.id,
            )
        metrics.record_transition(JobStatus.RUNNING, JobStatus.COMPLETED)
        metrics.mark_finished(job.id)
        job = store.update_job(
            job.id,
            status=JobStatus.COMPLETED,
            progress=100,
            asset_id=asset.id,
        )
        
    except Exception as exc:  # pragma: no cover - guard rail for demo
        job = store.update_job(job.id, status=JobStatus.FAILED, error=str(exc))
        async with SessionLocal() as session:
            await update_job_fields(session, job.id, status=JobStatus.FAILED, error=str(exc))
        metrics.record_transition(JobStatus.RUNNING, JobStatus.FAILED)
        metrics.mark_finished(job.id)
def _valid_url(u: str | None) -> bool:
    return isinstance(u, str) and (u.startswith("http://") or u.startswith("https://"))

