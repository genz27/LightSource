from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base with UTC timestamps."""

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[dt.datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
