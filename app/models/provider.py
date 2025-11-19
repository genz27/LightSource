from __future__ import annotations

from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Provider(Base):
    __tablename__ = "providers"

    name: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    models: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 可选的渠道访问令牌，由 admin 通过 /providers 管理接口配置；不会在对外 API 中回显
    api_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
