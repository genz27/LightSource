from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class AssetOut(BaseModel):
    id: str
    type: AssetType
    provider: Optional[str]
    url: str
    preview_url: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)
    is_public: bool = True
    created_at: dt.datetime
    owner_id: Optional[str] = None


class AssetList(BaseModel):
    items: list[AssetOut]
    total: int
    total_all: int | None = None
