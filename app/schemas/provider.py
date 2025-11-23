from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Capability(str, Enum):
    IMAGE = "image"
    IMAGE_EDIT = "image-edit"
    EDIT_IMAGE = "edit_image"
    CHAT_COMPLETIONS = "chat-completions"
    IMAGES_GENERATIONS = "images-generations"
    VIDEO = "video"


class ProviderInfo(BaseModel):
    name: str
    display_name: str
    models: List[str]
    capabilities: List[Capability]
    enabled: bool = True
    notes: Optional[str] = None
    base_url: Optional[str] = None
