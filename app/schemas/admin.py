from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AdminCreateUser(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern=r"^(user|admin)$")


class AdminRoleUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(user|admin)$")


class AdminWalletAdjust(BaseModel):
    amount: float
    description: str | None = None


class AdminUserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=2, max_length=50)


class AdminPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6)