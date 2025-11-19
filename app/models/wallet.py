from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, JSON, Numeric, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WalletTxTypeDB(str, enum.Enum):
    TOPUP = "topup"
    DEDUCT = "deduct"
    REFUND = "refund"
    ADJUST = "adjust"


class WalletTxStatusDB(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    frozen: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[WalletTxTypeDB] = mapped_column(Enum(WalletTxTypeDB), nullable=False)
    status: Mapped[WalletTxStatusDB] = mapped_column(Enum(WalletTxStatusDB), nullable=False, default=WalletTxStatusDB.COMPLETED)
    ref_job_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)