from __future__ import annotations

def api_error(message: str) -> dict:
    return {"error": {"message": message, "type": "client_error", "param": None, "code": None}}