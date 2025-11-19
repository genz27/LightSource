from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

from app.services.auth import hash_password, verify_password


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    role: str
    created_at: dt.datetime


class UserStore:
    def __init__(self) -> None:
        self.users: Dict[str, User] = {}

    def create_user(self, *, email: str, password: str, role: str | None = None) -> User:
        if any(u.email == email for u in self.users.values()):
            raise ValueError("email already exists")
        resolved_role = role or ("admin" if len(self.users) == 0 else "user")
        user = User(
            id=str(uuid.uuid4()),
            email=email.lower(),
            password_hash=hash_password(password),
            role=resolved_role,
            created_at=dt.datetime.utcnow(),
        )
        self.users[user.id] = user
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        email = email.lower()
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def verify_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if user and verify_password(password, user.password_hash):
            return user
        return None

    @staticmethod
    def is_admin(user: User | None) -> bool:
        return bool(user and user.role == "admin")


user_store = UserStore()


def get_user_store() -> UserStore:
    return user_store
