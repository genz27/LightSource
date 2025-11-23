from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.utils import api_error
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps.auth import get_current_user
from app.schemas import ProviderInfo, UserOut
from app.services.persistence import list_providers_db, update_provider_db, update_provider_secret_db, get_provider_by_name
import time
import requests

router = APIRouter()


@router.get("", response_model=list[ProviderInfo])
async def list_providers(session: AsyncSession = Depends(get_session)) -> list[ProviderInfo]:
    return await list_providers_db(session)


@router.patch("/{name}", response_model=ProviderInfo)
async def patch_provider(
    name: str,
    payload: dict,
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProviderInfo:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=api_error("Admin only"))
    provider = await update_provider_db(
        session,
        name=name,
        enabled=payload.get("enabled"),
        notes=payload.get("notes"),
        base_url=payload.get("base_url"),
        models=payload.get("models"),
        capabilities=payload.get("capabilities"),
    )
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Provider not found"))
    try:
        from app.services.audit import write as audit_write
        audit_write("provider.patch", {"name": name, "user_id": current_user.id, "changes": {k: payload.get(k) for k in ("enabled","notes","base_url","models","capabilities")}})
    except Exception:
        pass
    return provider


@router.patch("/{name}/secret", status_code=status.HTTP_204_NO_CONTENT)
async def patch_provider_secret(
    name: str,
    payload: dict,
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Admin-only endpoint to configure provider api_token (channel secret).

    The secret is stored in DB but never returned in any response.
    """

    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=api_error("Admin only"))
    api_token = payload.get("api_token")
    ok = await update_provider_secret_db(session, name=name, api_token=api_token)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Provider not found"))
    try:
        from app.services.audit import write as audit_write
        audit_write("provider.secret.patch", {"name": name, "user_id": current_user.id})
    except Exception:
        pass


@router.post("/{name}/test")
async def test_provider(
    name: str,
    current_user: UserOut = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=api_error("Admin only"))
    provider = await get_provider_by_name(session, name)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=api_error("Provider not found"))
    base = provider.base_url or ""
    if not base:
        return {"name": name, "status": "disabled", "reason": "missing base_url"}
    url = base if base.endswith("/") else base + "/"
    start = time.time()
    try:
        if name in ("flux", "majicflus"):
            resp = requests.get(url + "v1/models", headers={"Authorization": f"Bearer {provider.api_token}"} if provider.api_token else {}, timeout=10)
            ok = resp.status_code in (200, 401, 403)
        elif name == "sora2":
            resp = requests.get(url + "health", timeout=5)
            ok = resp.status_code in (200, 404)  # 某些实现可能无 /health
        else:
            resp = requests.head(url, timeout=5)
            ok = resp.status_code < 500
        latency = int((time.time() - start) * 1000)
        return {"name": name, "status": "ok" if ok else "unhealthy", "latency_ms": latency, "http": resp.status_code}
    except Exception as exc:
        latency = int((time.time() - start) * 1000)
        return {"name": name, "status": "error", "latency_ms": latency, "error": str(exc)}
