from __future__ import annotations

import asyncio
import datetime as dt
import re
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
from app.interface.registry import OpenAIImageAdapter, resolve_adapter
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
    sora_task: asyncio.Task | None = None
    provider_progress_val: float = 1.0
    loop = asyncio.get_running_loop()
    async def _apply_progress(val: float):
        v = float(max(1.0, min(95.0, val)))
        nonlocal job
        job = store.update_job(job.id, progress=v)
        async with SessionLocal() as session:
            await update_job_fields(session, job.id, progress=v)
    def _on_provider_progress(val: float):
        nonlocal provider_progress_val
        try:
            provider_progress_val = float(val)
            asyncio.run_coroutine_threadsafe(_apply_progress(val), loop)
        except Exception:
            pass
    attempted_external = False
    async with SessionLocal() as session:
        provider = await get_provider_by_name(session, job.provider) if job.provider else None
    adapter = resolve_adapter(provider) if provider and provider.enabled else None
    provider_caps = {c.lower() for c in (provider.capabilities or [])} if provider else set()
    image_api_style = _image_api_style(provider_caps)
    if adapter and job.kind == JobKind.TEXT_TO_IMAGE and provider and ("image" in provider_caps or "image-edit" in provider_caps or "edit_image" in provider_caps):
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
        primary_image = src_url or (src_urls[0] if isinstance(src_urls, list) and src_urls else None)
        supports_image_edit = "image-edit" in provider_caps or "edit_image" in provider_caps
        supports_image_url = provider.name in {"sora", "nano-banana-2"} or (
            isinstance(adapter, OpenAIImageAdapter) and image_api_style == "chat-completions"
        )
        use_edit = bool(primary_image) and (
            supports_image_edit or (job.model or "").startswith("qwen-image-edit") or ("edit" in (job.model or ""))
        )
        model_to_use = _select_model(provider.models or [], job.model, use_edit)

        if use_edit and hasattr(adapter, "edit_image"):
            qwen_task = asyncio.create_task(
                asyncio.to_thread(
                    adapter.edit_image,
                    src_urls if isinstance(src_urls, list) and src_urls else (src_url or ""),
                    job.prompt,
                    model=model_to_use,
                    api_key=provider.api_token,
                    base_url=provider.base_url or "",
                    size=job.params.size,
                    api_style=image_api_style if isinstance(adapter, OpenAIImageAdapter) else None,
                )
            )
        elif supports_image_url:
            qwen_task = asyncio.create_task(
                asyncio.to_thread(
                    adapter.generate_image,
                    job.prompt,
                    model=model_to_use,
                    api_key=provider.api_token,
                    base_url=provider.base_url or "",
                    size=job.params.size,
                    image_url=primary_image or None,
                    api_style=image_api_style if isinstance(adapter, OpenAIImageAdapter) else None,
                )
            )
        else:
            qwen_task = asyncio.create_task(
                asyncio.to_thread(
                    adapter.generate_image,
                    job.prompt,
                    model=model_to_use,
                    api_key=provider.api_token,
                    base_url=provider.base_url or "",
                    size=job.params.size,
                    api_style=image_api_style if isinstance(adapter, OpenAIImageAdapter) else None,
                )
            )

    vendor_video_id: str | None = None
    if provider and provider.enabled and adapter and job.kind in {JobKind.TEXT_TO_VIDEO, JobKind.IMAGE_TO_VIDEO}:
        attempted_external = True
        resolution_boot = job.params.size or (
            "1024x576" if (job.params.orientation or "landscape") == "landscape" else "576x1024"
        )
        orientation_str = (job.params.orientation.value if job.params.orientation else None)
        m_eff = job.model or ""
        if m_eff and ("sora-video" in m_eff):
            model_to_send = m_eff
        else:
            model_to_send = (
                f"sora-video-{orientation_str}" if orientation_str in ("landscape", "portrait") else (job.model or "sora2-video")
            )
        duration_eff = 6
        try:
            m_lower = (model_to_send or "").lower()
            if "10s" in m_lower:
                duration_eff = 10
            elif "15s" in m_lower:
                duration_eff = 15
        except Exception:
            duration_eff = 6
        src_url_boot = job.params.extras.get("source_image_url") if job.params and job.params.extras else None
        try:
            base_eff = provider.base_url
            if not base_eff or ("sora2.example" in str(base_eff).lower() or str(base_eff).lower().endswith(".example")):
                base_eff = None
            sora_task = asyncio.create_task(
                asyncio.to_thread(
                    adapter.create_video,
                    job.prompt,
                    model=model_to_send,
                    image=(src_url_boot or None),
                    api_key=provider.api_token,
                    base_url=base_eff,
                    debug=getattr(store, "debug_enabled", False),
                    duration_seconds=duration_eff,
                    resolution=resolution_boot,
                    on_progress=_on_provider_progress,
                )
            )
            provider_response_boot = {
                "provider": "sora2",
                "model": model_to_send,
                "status": "processing",
                "orientation": orientation_str,
                "duration_seconds": duration_eff,
                "resolution": resolution_boot,
                "raw": {"boot": True},
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
            tgt = float(max(progress, provider_progress_val, float(job.progress or 0)))
            job = store.update_job(job.id, progress=tgt)
            async with SessionLocal() as session:
                await update_job_fields(session, job.id, progress=tgt)
        

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

        if provider and provider.enabled and adapter and job.kind in {JobKind.TEXT_TO_VIDEO, JobKind.IMAGE_TO_VIDEO} and sora_task is not None:
            attempted_external = True
            resolution = job.params.size or ("1024x576" if (job.params.orientation or "landscape") == "landscape" else "576x1024")
            duration_seconds = 6
            try:
                m_lower = str(job.model or "").lower()
                if "10s" in m_lower:
                    duration_seconds = 10
                elif "15s" in m_lower:
                    duration_seconds = 15
            except Exception:
                duration_seconds = 6
            try:
                data_done = await sora_task
                video_url = (data_done or {}).get("video_url") or (data_done or {}).get("result_url")
                provider_response = {
                    "provider": "sora2",
                    "model": (data_done or {}).get("model") or (job.model or "sora2-video"),
                    "status": (data_done or {}).get("status") or ("succeeded" if video_url else "processing"),
                    "orientation": (job.params.orientation.value if job.params.orientation else None),
                    "duration_seconds": duration_seconds,
                    "resolution": resolution,
                    "raw": data_done,
                }
                if provider_response and video_url:
                    image_url = video_url
            except Exception:
                pass

        # finish + create asset record with enriched meta and audit info
        is_image = job.kind == JobKind.TEXT_TO_IMAGE
        frames = 1 if is_image else 20
        duration_seconds = 0 if is_image else 6
        if not is_image:
            try:
                m_lower = str(job.model or "").lower()
                if "10s" in m_lower:
                    duration_seconds = 10
                elif "15s" in m_lower:
                    duration_seconds = 15
            except Exception:
                pass
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
        try:
            raw = provider_response.get("raw") if isinstance(provider_response, dict) else None
            dbg = raw.get("debug") if isinstance(raw, dict) else None
            if dbg:
                extras["provider_debug"] = dbg
        except Exception:
            pass
        params.extras = extras
        job = store.update_job(job.id, params=params)
        async with SessionLocal() as session:
            await update_job_fields(session, job.id, params=params.dict() if hasattr(params, "dict") else params)

        normalized_url = _normalize_output_url(image_url)

        if attempted_external and not normalized_url:
            err_payload = provider_response
            try:
                extras = job.params.extras if job.params and job.params.extras else {}
                boot = extras.get("provider_response")
                if boot:
                    err_payload = boot
            except Exception:
                pass
            async with SessionLocal() as session:
                await update_job_fields(session, job.id, status=JobStatus.FAILED, error=str(err_payload))
            metrics.record_transition(JobStatus.RUNNING, JobStatus.FAILED)
            metrics.mark_finished(job.id)
            store.update_job(job.id, status=JobStatus.FAILED, error=str(err_payload))
            return
        output_url = normalized_url or placeholder_output(job.kind.value, job.id)[1]

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


_DATA_URL_RE = re.compile(r"^data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\r\n]+$")
_BASE64_RE = re.compile(r"^[A-Za-z0-9+/=\r\n]+$")


def _normalize_output_url(u: str | None) -> str | None:
    """Accept HTTP(S) URLs and inline base64 image data.

    Providers may return:
    - http/https URLs
    - data:image;base64 URLs
    - raw base64 payloads (e.g., b64_json from /v1/images/generations)
    """

    if not isinstance(u, str):
        return None

    val = u.strip()
    if not val:
        return None

    if val.startswith("http://") or val.startswith("https://"):
        return val

    if _DATA_URL_RE.match(val):
        return val

    if len(val) > 100 and _BASE64_RE.match(val):
        return f"data:image/png;base64,{val}"

    return None


def _image_api_style(capabilities: set[str]) -> str:
    """Return preferred image API style for OpenAI-compatible providers."""

    caps = {c.lower() for c in capabilities}
    if "images-generations" in caps:
        return "images-generations"
    if "chat-completions" in caps:
        return "chat-completions"
    return "chat-completions"


def _select_model(provider_models: list[str], requested: str | None, use_edit: bool) -> str:
    """Pick a provider model that matches the intended flow (generate vs edit).

    - If the caller requested a model, prefer it unless it mismatches the flow and
      a better-suited model exists in the provider list.
    - Otherwise, choose the first matching model by capability (edit vs generate),
      falling back to the provider's first declared model.
    """

    requested = (requested or "").strip()
    if requested:
        req_lower = requested.lower()
        wants_edit = "edit" in req_lower
        if use_edit and not wants_edit:
            alt = _first_model(provider_models, want_edit=True)
            if alt:
                return alt
        if not use_edit and wants_edit:
            alt = _first_model(provider_models, want_edit=False)
            if alt:
                return alt
        return requested

    fallback = _first_model(provider_models, want_edit=use_edit)
    return fallback or (provider_models[0] if provider_models else "")


def _first_model(models: list[str], *, want_edit: bool) -> str | None:
    for model in models:
        model_lower = model.lower()
        has_edit = "edit" in model_lower
        if want_edit and has_edit:
            return model
        if not want_edit and not has_edit:
            return model
    return None


def _image_api_style(capabilities: set[str]) -> str:
    """Return preferred image API style for OpenAI-compatible providers."""

    caps = {c.lower() for c in capabilities}
    if "images-generations" in caps:
        return "images-generations"
    if "chat-completions" in caps:
        return "chat-completions"
    return "chat-completions"


def _select_model(provider_models: list[str], requested: str | None, use_edit: bool) -> str:
    """Pick a provider model that matches the intended flow (generate vs edit).

    - If the caller requested a model, prefer it unless it mismatches the flow and
      a better-suited model exists in the provider list.
    - Otherwise, choose the first matching model by capability (edit vs generate),
      falling back to the provider's first declared model.
    """

    requested = (requested or "").strip()
    if requested:
        req_lower = requested.lower()
        wants_edit = "edit" in req_lower
        if use_edit and not wants_edit:
            alt = _first_model(provider_models, want_edit=True)
            if alt:
                return alt
        if not use_edit and wants_edit:
            alt = _first_model(provider_models, want_edit=False)
            if alt:
                return alt
        return requested

    fallback = _first_model(provider_models, want_edit=use_edit)
    return fallback or (provider_models[0] if provider_models else "")


def _first_model(models: list[str], *, want_edit: bool) -> str | None:
    for model in models:
        model_lower = model.lower()
        has_edit = "edit" in model_lower
        if want_edit and has_edit:
            return model
        if not want_edit and not has_edit:
            return model
    return None

