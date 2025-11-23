from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Tuple

import requests

DEFAULT_BASE_URL = "https://api.airgzn.top"
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


_DATA_URL_RE = re.compile(r"data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\r\n]+")
_HTTP_URL_RE = re.compile(r"https?://\S+")


def _find_media_url(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    data_match = _DATA_URL_RE.search(text)
    if data_match:
        return data_match.group(0)
    http_match = _HTTP_URL_RE.search(text)
    if http_match:
        return http_match.group(0)
    return None


def _search_media_in_obj(obj: Any) -> str | None:
    # Search nested structures for an HTTP or data URL embedded anywhere.
    if isinstance(obj, str):
        return _find_media_url(obj)
    if isinstance(obj, list):
        for item in obj:
            url_val = _search_media_in_obj(item)
            if url_val:
                return url_val
        return None
    if isinstance(obj, dict):
        # Prefer explicit url fields when present.
        url_val = obj.get("url")
        if isinstance(url_val, str):
            cleaned = _find_media_url(url_val) or url_val
            if cleaned:
                return cleaned
        # Common content-like fields where providers may embed markdown URLs.
        for key in ("image_url", "text", "content", "parts"):
            if key in obj:
                url_val = _search_media_in_obj(obj[key])
                if url_val:
                    return url_val
        # Fallback: scan remaining values.
        for value in obj.values():
            url_val = _search_media_in_obj(value)
            if url_val:
                return url_val
    return None


def _clean_url(url_val: str) -> str:
    return url_val.rstrip(")].>,\"'")


def _extract_url_from_parts(parts: Iterable[Any]) -> str | None:
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "image_url":
            image_entry = part.get("image_url")
            if isinstance(image_entry, dict):
                url_val = image_entry.get("url")
                if isinstance(url_val, str):
                    return _clean_url(url_val)
            if isinstance(image_entry, str):
                return _clean_url(image_entry)
        if part.get("type") == "text":
            text = part.get("text")
            url_val = _find_media_url(text)
            if url_val:
                return _clean_url(url_val)
        url_val = _search_media_in_obj(part)
        if url_val:
            return _clean_url(url_val)
    return None


def _extract_image_url(message: dict[str, Any]) -> str:
    content = message.get("content")
    # New-style content parts
    if isinstance(content, list):
        url_val = _extract_url_from_parts(content)
        if url_val:
            return _clean_url(url_val)
    # Legacy single string content
    if isinstance(content, str):
        url_val = _find_media_url(content)
        if url_val:
            return _clean_url(url_val)
    # Other nested structures (dict, mixed content)
    url_val = _search_media_in_obj(content)
    if url_val:
        return _clean_url(url_val)
    raise RuntimeError("provider returned no image URL in message content")


def _extract_from_stream(resp: requests.Response) -> Tuple[str | None, list[dict[str, Any]]]:
    chunks: list[dict[str, Any]] = []
    last_url: str | None = None
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        line = raw.strip()
        if not line or not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            obj = json.loads(payload)
        except Exception:
            url_val = _find_media_url(payload)
            if url_val:
                last_url = _clean_url(url_val)
            continue
        if isinstance(obj, dict):
            chunks.append(obj)
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if isinstance(content, list):
                url_val = _extract_url_from_parts(content)
                if url_val:
                    last_url = _clean_url(url_val)
                    break
            if isinstance(content, str):
                url_val = _find_media_url(content)
                if url_val:
                    last_url = _clean_url(url_val)
                    break
            url_val = _search_media_in_obj(content)
            if url_val:
                last_url = _clean_url(url_val)
                break
    return last_url, chunks


def _build_content(prompt: str, image_url: str | None) -> List[Dict[str, Any]] | str:
    if image_url:
        return [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    return prompt


def generate_image(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None,
    base_url: str | None = None,
    size: str | None = None,
    image_url: str | None = None,
) -> Tuple[str, Dict[str, Any]]:
    url = _normalize_base_url(base_url)
    stream = bool(image_url)
    payload: Dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {
                "role": "user",
                "content": _build_content(prompt, image_url),
            }
        ],
        "stream": stream,
    }
    if size:
        payload["size"] = size
    response = requests.post(
        f"{url}v1/chat/completions",
        headers=_headers(api_key),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=120,
        stream=stream,
    )
    response.raise_for_status()

    provider_response: Dict[str, Any] = {
        "provider": "nano-banana-2",
        "model": payload["model"],
        "request": payload,
    }

    if stream:
        image_out, chunks = _extract_from_stream(response)
        provider_response["raw"] = {"stream": True, "chunks": chunks}
        if not image_out:
            raise RuntimeError("provider returned no image URL in stream")
        return image_out, provider_response

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("provider returned no choices")
    message = choices[0].get("message") or {}
    image_out = _extract_image_url(message)

    provider_response["raw"] = data
    return image_out, provider_response
