from __future__ import annotations

import datetime as dt
from pydantic import BaseModel


class PreferencesOut(BaseModel):
    owner_id: str
    theme: str
    language: str
    notifications: bool
    updated_at: dt.datetime
    meta: dict


class PreferencesUpdate(BaseModel):
    theme: str
    language: str
    notifications: bool
    meta: dict | None = None