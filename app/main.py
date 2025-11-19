"""FastAPI application bootstrap for LightSource backend.

Queue-less implementation with in-memory state and simulated generation to match
the frontend demos. Swap out services later for real providers or persistence.
"""

from __future__ import annotations

import asyncio
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from starlette.responses import JSONResponse, FileResponse, RedirectResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.api import assets, auth, jobs, providers
from app.api import images, videos
from app.api import billing, preferences as preferences_api
from app.api import admin
from app.db import engine, ensure_database_and_schema
from app.models import asset, job, provider, user, wallet, preferences as preferences_model  # noqa: F401
from app.models.base import Base
from app.services.metrics import metrics
from app.services.taskqueue import get_task_queue
from app.services.store import get_store


def create_app() -> FastAPI:
    app = FastAPI(title="LightSource API", version="0.1.0")

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # 简易限流：滑动窗口 + 突发控制（内存）
    rate_state: dict[str, list[float]] = {}

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        path = request.url.path
        if not (path.startswith("/jobs") or path.startswith("/v1/images") or path.startswith("/v1/videos")):
            return await call_next(request)
        now = asyncio.get_event_loop().time()
        key_parts = [request.client.host or "unknown"]
        auth = request.headers.get("authorization") or ""
        if auth.lower().startswith("bearer "):
            key_parts.append("user")
        rl_key = ":".join(key_parts)
        window = 60.0
        limit = settings.rate_limit_per_minute
        burst = settings.burst_limit
        bucket = rate_state.get(rl_key, [])
        bucket = [t for t in bucket if now - t <= window]
        if len(bucket) >= max(limit, burst):
            metrics.rate_limited_total += 1
            return JSONResponse(status_code=429, content={"error": {"message": "rate limit exceeded", "type": "client_error", "param": None, "code": None}})
        bucket.append(now)
        rate_state[rl_key] = bucket
        metrics.requests_total += 1
        return await call_next(request)

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(assets.router, prefix="/api/assets", tags=["assets"])
    app.include_router(images.router, prefix="/api/v1", tags=["images"])
    app.include_router(videos.router, prefix="/api/v1", tags=["videos"])
    app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
    app.include_router(preferences_api.router, prefix="/api/preferences", tags=["preferences"]) 
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"]) 

    app.mount("/media", StaticFiles(directory=settings.storage_base, check_dir=False), name="media")

    frontend_root = settings.frontend_dist or "lightsource-vue/dist"
    app.mount("/assets", StaticFiles(directory=Path(frontend_root) / "assets", check_dir=False), name="assets")
    try:
        app.mount("/favicon.ico", StaticFiles(directory=frontend_root, check_dir=False), name="favicon")
    except Exception:
        pass

    @app.get("/", tags=["home"], include_in_schema=False)
    async def home():
        try:
            return FileResponse(Path(frontend_root) / "index.html")
        except Exception:
            return RedirectResponse(url="/docs")

    @app.get("/api/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/metrics", tags=["metrics"])
    async def get_metrics() -> dict:
        return metrics.snapshot()

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        await asyncio.sleep(0)

    @app.on_event("startup")
    async def startup_event() -> None:
        await ensure_database_and_schema()
        store = get_store()
        tq = get_task_queue()
        await tq.start(store)
        try:
            from app.services.persistence import list_jobs_db, update_job_fields
            from app.schemas import JobStatus
            from app.db import SessionLocal
            async with SessionLocal() as session:
                jobs = await list_jobs_db(session)
                for j in jobs:
                    if j.status in {JobStatus.RUNNING, JobStatus.QUEUED}:
                        await update_job_fields(session, j.id, status=JobStatus.QUEUED)
                        await tq.enqueue(j.id)
        except Exception:
            pass

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("media/") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi"):
            return JSONResponse({"error": "not found"}, status_code=404)
        try:
            return FileResponse(Path(frontend_root) / "index.html")
        except Exception:
            return RedirectResponse(url="/docs")

    return app

app = create_app()
