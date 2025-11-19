from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import secrets
from typing import Any, Dict, Optional, Tuple

from app.config import get_settings


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return _b64encode(salt) + "." + _b64encode(dk)


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt_b64, dk_b64 = hashed.split(".")
        salt = _b64decode(salt_b64)
        expected = _b64decode(dk_b64)
        test = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return hmac.compare_digest(expected, test)
    except Exception:
        return False


def _sign(payload: Dict[str, Any], exp_minutes: int) -> str:
    settings = get_settings()
    header = {"alg": "HS256", "typ": "JWT"}
    now = dt.datetime.utcnow()
    payload = payload.copy()
    payload["exp"] = int((now + dt.timedelta(minutes=exp_minutes)).timestamp())
    segments = [
        _b64encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    signature = hmac.new(settings.jwt_secret.encode(), signing_input, hashlib.sha256).digest()
    segments.append(_b64encode(signature))
    return ".".join(segments)


def _decode(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode()
        signature = _b64decode(sig_b64)
        expected = hmac.new(settings.jwt_secret.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        payload = json.loads(_b64decode(payload_b64))
        exp = payload.get("exp")
        if exp is not None and int(dt.datetime.utcnow().timestamp()) > int(exp):
            raise ValueError("token expired")
        return payload
    except Exception as exc:
        raise ValueError("invalid token") from exc


def create_tokens(sub: str) -> Tuple[str, str]:
    settings = get_settings()
    access = _sign({"sub": sub, "type": "access"}, settings.jwt_access_minutes)
    refresh = _sign({"sub": sub, "type": "refresh"}, settings.jwt_refresh_minutes)
    return access, refresh


def decode_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    payload = _decode(token)
    if payload.get("type") != token_type:
        raise ValueError("invalid token type")
    return payload
