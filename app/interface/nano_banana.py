from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple

import requests

DEFAULT_BASE_URL = "https://api.nano-banana-2.example"
DEFAULT_MODEL = "gemini-3-pro-image-preview"


def _headers(api_key: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _normalize_base_url(base_url: str | None) -> str:
    url = base_url or DEFAULT_BASE_URL
    if not url.endswith("/"):
        url = url + "/"
    return url


def _extract_image_url(message: dict[str, Any]) -> str:
    content = message.get("content")
    # New-style content parts
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "image_url":
                image_entry = part.get("image_url")
                if isinstance(image_entry, str):
                    return image_entry
                if isinstance(image_entry, dict):
                    url = image_entry.get("url")
                    if isinstance(url, str):
                        return url
            if part.get("type") == "text":
                text = part.get("text")
                if isinstance(text, str):
                    match = re.search(r"https?://\S+", text)
                    if match:
                        return match.group(0)
    # Legacy single string content
    if isinstance(content, str):
        match = re.search(r"https?://\S+", content)
        if match:
            return match.group(0)
    raise RuntimeError("provider returned no image URL in message content")


def generate_image(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None,
    base_url: str | None = None,
    size: str | None = None,
) -> Tuple[str, Dict[str, Any]]:
    url = _normalize_base_url(base_url)
    payload: Dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
    }
    if size:
        payload["size"] = size
    response = requests.post(
        f"{url}v1/chat/completions",
        headers=_headers(api_key),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("provider returned no choices")
    message = choices[0].get("message") or {}
    image_url = _extract_image_url(message)

    provider_response: Dict[str, Any] = {
        "provider": "nano-banana-2",
        "model": payload["model"],
        "request": payload,
        "raw": data,
    }
    return image_url, provider_response
