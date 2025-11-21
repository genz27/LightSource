from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Tuple

import requests

DEFAULT_BASE_URL = "http://localhost:8000/"
DEFAULT_MODEL = "sora-image"


def _headers(api_key: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _normalize_base_url(url: str | None) -> str:
    url = url or DEFAULT_BASE_URL
    return url if url.endswith("/") else url + "/"


def _build_content(prompt: str, image_url: str | None) -> List[Dict[str, Any]] | str:
    if image_url:
        return [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    return prompt


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
            if isinstance(text, str):
                match = re.search(r"https?://\S+", text)
                if match:
                    return _clean_url(match.group(0))
    return None


def _extract_image_url(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, list):
        url_val = _extract_url_from_parts(content)
        if url_val:
            return _clean_url(url_val)
    if isinstance(content, str):
        match = re.search(r"https?://\S+", content)
        if match:
            return _clean_url(match.group(0))
    raise RuntimeError("provider returned no image URL in message content")


def _extract_from_stream(resp: requests.Response) -> Tuple[str | None, list[dict[str, Any]]]:
    chunks: list[dict[str, Any]] = []
    last_url: str | None = None
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        line = raw.strip()
        if not line:
            continue
        if not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if data_str == "[DONE]":
            break
        try:
            obj = json.loads(data_str)
        except Exception:
            match = re.search(r"https?://\S+", data_str)
            if match:
                last_url = _clean_url(match.group(0))
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
                    last_url = url_val
                    break
            if isinstance(content, str):
                match = re.search(r"https?://\S+", content)
                if match:
                    last_url = _clean_url(match.group(0))
                    break
    return last_url, chunks


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
        "provider": "sora",
        "model": payload["model"],
        "request": payload,
    }

    if stream:
        image_url_val, chunks = _extract_from_stream(response)
        provider_response["raw"] = {"stream": True, "chunks": chunks}
        if not image_url_val:
            raise RuntimeError("provider returned no image URL in stream")
        return image_url_val, provider_response

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("provider returned no choices")
    message = choices[0].get("message") or {}
    image_url_val = _extract_image_url(message)
    provider_response["raw"] = data
    return image_url_val, provider_response

