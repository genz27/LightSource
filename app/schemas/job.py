from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobKind(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class Orientation(str, Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


class JobParams(BaseModel):
    orientation: Optional[Orientation] = Field(None, description="Video orientation")
    size: Optional[str] = Field(None, description="Resolution, e.g., 1024x1024")
    seed: Optional[int] = Field(None, description="Random seed for generation")
    style: Optional[str] = Field(None, description="Style preset")
    guidance: Optional[float] = Field(None, description="Guidance strength")
    extras: dict[str, Any] = Field(default_factory=dict)


class JobCreate(BaseModel):
    prompt: str = Field(..., min_length=1)
    kind: JobKind
    model: Optional[str] = None
    provider: Optional[str] = None
    is_public: bool = True
    params: JobParams = Field(default_factory=JobParams)
    source_image_name: Optional[str] = None
    owner_id: Optional[str] = None


class JobOut(BaseModel):
    id: str
    prompt: str
    kind: JobKind
    model: Optional[str]
    provider: Optional[str]
    is_public: bool
    params: JobParams
    status: JobStatus
    progress: int
    asset_id: Optional[str]
    error: Optional[str]
    created_at: dt.datetime
    updated_at: dt.datetime
    owner_id: Optional[str] = None


class JobList(BaseModel):
    items: list[JobOut]
    total: int
    total_all: int | None = None


class JobStatusOut(BaseModel):
    id: str
    status: JobStatus
    progress: int
    asset_id: Optional[str]
    error: Optional[str]
    updated_at: dt.datetime
