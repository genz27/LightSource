from __future__ import annotations

import datetime as dt
from enum import Enum
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    TOPUP = "topup"
    DEDUCT = "deduct"
    REFUND = "refund"
    ADJUST = "adjust"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class WalletOut(BaseModel):
    owner_id: str
    balance: float
    currency: str
    frozen: float
    updated_at: dt.datetime


class WalletTxOut(BaseModel):
    id: str
    user_id: str
    amount: float
    type: TransactionType
    status: TransactionStatus
    ref_job_id: str | None = None
    description: str | None = None
    meta: dict = Field(default_factory=dict)
    created_at: dt.datetime


class TopUpRequest(BaseModel):
    amount: float


class DeductRequest(BaseModel):
    amount: float
    ref_job_id: str | None = None
    description: str | None = None