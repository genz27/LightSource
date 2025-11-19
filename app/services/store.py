from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import uuid

from app.schemas import AssetOut, AssetType, JobCreate, JobKind, JobOut, JobParams, JobStatus
from app.config import get_settings


class MemoryStore:
    """In-memory store to avoid a database while prototyping."""

    def __init__(self) -> None:
        self.jobs: Dict[str, JobOut] = {}
        self.assets: Dict[str, AssetOut] = {}
        self._job_counter = 230
        self._asset_counter = 0
        self._job_id_prefix = "job_"
        self.job_assets: defaultdict[str, str] = defaultdict(str)
        try:
            self.debug_enabled: bool = bool(getattr(get_settings(), "debug", False))
        except Exception:
            self.debug_enabled = False

    def _next_job_id(self) -> str:
        self._job_counter += 1
        return f"{self._job_id_prefix}{self._job_counter}"

    def _next_asset_id(self) -> str:
        return f"asset_{uuid.uuid4().hex[:8]}"

    def create_job(self, data: JobCreate, job_id: str | None = None) -> JobOut:
        now = dt.datetime.utcnow()
        job_id = job_id or self._next_job_id()
        job = JobOut(
            id=job_id,
            prompt=data.prompt,
            kind=data.kind,
            model=data.model,
            provider=data.provider,
            is_public=data.is_public,
            params=data.params or JobParams(),
            status=JobStatus.QUEUED,
            progress=0,
            asset_id=None,
            error=None,
            created_at=now,
            updated_at=now,
            owner_id=data.owner_id,
        )
        self.jobs[job_id] = job
        return job

    def update_job(self, job_id: str, **fields) -> JobOut:
        job = self.jobs[job_id]
        updated = job.copy(update={**fields, "updated_at": dt.datetime.utcnow()})
        self.jobs[job_id] = updated
        return updated

    def list_jobs(self) -> Tuple[List[JobOut], int]:
        items = sorted(self.jobs.values(), key=lambda j: j.created_at, reverse=True)
        return items, len(items)

    def get_job(self, job_id: str) -> Optional[JobOut]:
        return self.jobs.get(job_id)

    def create_asset(
        self,
        *,
        kind: JobKind,
        provider: str | None,
        is_public: bool,
        meta: dict,
        url: str | None = None,
        preview_url: str | None = None,
        owner_id: str | None = None,
    ) -> AssetOut:
        now = dt.datetime.utcnow()
        asset_type = AssetType.IMAGE if kind == JobKind.TEXT_TO_IMAGE else AssetType.VIDEO
        if url is None:
            ext = "png" if asset_type == AssetType.IMAGE else "mp4"
            asset_id = self._next_asset_id()
            url = f"https://cdn.lightsource.local/{asset_id}.{ext}"
            preview_url = url if asset_type == AssetType.IMAGE else f"{url}#preview"
        else:
            asset_id = self._next_asset_id()
            preview_url = preview_url or url
        asset = AssetOut(
            id=asset_id,
            type=asset_type,
            provider=provider,
            url=url,
            preview_url=preview_url,
            meta=meta or {},
            is_public=is_public,
            created_at=now,
            owner_id=owner_id,
        )
        self.assets[asset_id] = asset
        return asset

    def list_assets(
        self, *, asset_type: Optional[AssetType] = None, provider: Optional[str] = None, public_only: bool | None = None
    ) -> Tuple[List[AssetOut], int]:
        items = list(self.assets.values())
        if asset_type:
            items = [a for a in items if a.type == asset_type]
        if provider:
            items = [a for a in items if a.provider == provider]
        if public_only is not None:
            items = [a for a in items if a.is_public == public_only]
        items = sorted(items, key=lambda a: a.created_at, reverse=True)
        return items, len(items)

    def delete_asset(self, asset_id: str) -> bool:
        return self.assets.pop(asset_id, None) is not None

    # Runtime flags
    def set_debug(self, enabled: bool) -> None:
        self.debug_enabled = bool(enabled)

    def get_debug(self) -> bool:
        return bool(self.debug_enabled)

    def set_prices(self, prices: dict | None) -> None:
        base = {
            "text_to_image": 5.0,
            "image_to_image": 5.0,
            "text_to_video": 20.0,
            "image_to_video": 12.0,
        }
        if not isinstance(prices, dict):
            self.prices = base
            return
        merged = dict(base)
        for k, v in prices.items():
            try:
                fv = float(v)
                if fv < 0:
                    continue
                if k in base:
                    merged[k] = fv
            except Exception:
                continue
        self.prices = merged

    def get_prices(self) -> dict:
        try:
            p = getattr(self, "prices", None)
            if not isinstance(p, dict):
                self.set_prices(None)
                p = getattr(self, "prices", {})
            return p
        except Exception:
            return {"text_to_image": 5.0, "text_to_video": 20.0, "image_to_video": 12.0}


store = MemoryStore()


def get_store() -> MemoryStore:
    return store
