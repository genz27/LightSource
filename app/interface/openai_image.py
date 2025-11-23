from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Tuple

import requests

DEFAULT_BASE_URL = "https://api.generic-openai-image.example"
DEFAULT_MODEL = "generic-image-model"


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


_DATA_URL_RE = re.compile(r"data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\r\n]+")
_HTTP_URL_RE = re.compile(r"https?://\S+")


def _clean_url(url_val: str) -> str:
    return url_val.rstrip(")].>,\"'")


def _find_media_url(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    data_match = _DATA_URL_RE.search(text)
    if data_match:
        return _clean_url(data_match.group(0))
    http_match = _HTTP_URL_RE.search(text)
    if http_match:
        return _clean_url(http_match.group(0))
    return None


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
                return url_val
    return None


def _extract_image_url(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, list):
        url_val = _extract_url_from_parts(content)
        if url_val:
            return _clean_url(url_val)
    if isinstance(content, str):
        url_val = _find_media_url(content)
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
                last_url = url_val
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
                url_val = _find_media_url(content)
                if url_val:
                    last_url = url_val
                    break
    return last_url, chunks


def _build_content(prompt: str, image_url: str | None) -> List[Dict[str, Any]] | str:
    if image_url:
        return [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
    return prompt


def _build_edit_content(prompt: str, images: list[str]) -> List[Dict[str, Any]]:
    parts: list[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    for url in images:
        parts.append({"type": "image_url", "image_url": {"url": url}})
    return parts


def _generate_via_images_api(
    prompt: str,
    *,
    model: str | None,
    api_key: str | None,
    base_url: str | None,
    size: str | None,
    provider_name: str,
) -> Tuple[str, Dict[str, Any]]:
    url = _normalize_base_url(base_url)
    payload: Dict[str, Any] = {"model": model or DEFAULT_MODEL, "prompt": prompt}
    if size:
        payload["size"] = size

    response = requests.post(
        f"{url}v1/images/generations",
        headers=_headers(api_key),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    image_out: str | None = None
    try:
        choices = data.get("data") or []
        if isinstance(choices, list) and choices:
            first = choices[0] or {}
            url_val = first.get("url")
            if isinstance(url_val, str):
                image_out = _clean_url(url_val)
            elif isinstance(first.get("b64_json"), str):
                image_out = first.get("b64_json")
    except Exception:
        image_out = None

    provider_response: Dict[str, Any] = {
        "provider": provider_name,
        "model": payload["model"],
        "request": payload,
        "raw": data,
    }

    if not image_out:
        raise RuntimeError("provider returned no image URL in response")
    return image_out, provider_response


def generate_image(
    prompt: str,
    *,
    model: str | None,
    api_key: str | None,
    base_url: str | None = None,
    size: str | None = None,
    image_url: str | None = None,
    provider_name: str = "openai-compatible",
    temperature: float | None = 1,
    top_p: float | None = 1,
    stream_options: dict[str, Any] | None = None,
    stream: bool | None = None,
    api_style: str | None = None,
) -> Tuple[str, Dict[str, Any]]:
    style = (api_style or "chat-completions").lower()
    if style == "images-generations":
        return _generate_via_images_api(
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            size=size,
            provider_name=provider_name,
        )

    url = _normalize_base_url(base_url)
    stream = bool(image_url) if stream is None else bool(stream)
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
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if stream or stream_options:
        payload["stream_options"] = stream_options or {"include_usage": True}
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
        "provider": provider_name,
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


def edit_image(
    image_url: list[str] | str,
    prompt: str,
    *,
    model: str | None,
    api_key: str | None,
    base_url: str | None = None,
    size: str | None = None,
    provider_name: str = "openai-compatible",
    temperature: float | None = 1,
    top_p: float | None = 1,
    stream_options: dict[str, Any] | None = None,
    api_style: str | None = None,
) -> Tuple[str, Dict[str, Any]]:
    style = (api_style or "chat-completions").lower()
    if style == "images-generations":
        raise ValueError("image edits are not supported via /v1/images/generations")

    urls: list[str] = []
    if isinstance(image_url, list):
        urls = [u for u in image_url if isinstance(u, str) and u]
    elif isinstance(image_url, str):
        urls = [image_url]
    if not urls:
        raise ValueError("image_url is required for edit_image")

    url = _normalize_base_url(base_url)
    payload: Dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {
                "role": "user",
                "content": _build_edit_content(prompt, urls),
            }
        ],
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if stream_options:
        payload["stream_options"] = stream_options
    if size:
        payload["size"] = size

    response = requests.post(
        f"{url}v1/chat/completions",
        headers=_headers(api_key),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("provider returned no choices")
    message = choices[0].get("message") or {}
    image_out = _extract_image_url(message)

    provider_response: Dict[str, Any] = {
        "provider": provider_name,
        "model": payload["model"],
        "request": payload,
        "raw": data,
    }
    return image_out, provider_response
