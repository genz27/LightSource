from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Tuple

import requests
import time
from app.config import get_settings

DEFAULT_BASE_URL = "https://api.airgzn.top/"
DEFAULT_MODEL = "gemini-2.5-flash-image"


def _headers(api_key: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        _dbg("headers_prepared", {"keys": list(headers.keys())})
    except Exception:
        pass
    return headers


def _normalize_base_url(url: str | None) -> str:
    u = url or DEFAULT_BASE_URL
    if isinstance(u, str):
        u = u.strip().strip("`'\"")
    out = u if u.endswith("/") else u + "/"
    try:
        _dbg("normalize_base_url", {"in": url, "out": out})
    except Exception:
        pass
    return out


def _resolve_chat_endpoint(base_url: str | None) -> str:
    u = base_url or DEFAULT_BASE_URL
    if isinstance(u, str):
        u = u.strip().strip("`'\"")
    if "chat/completions" in u.lower():
        try:
            _dbg("resolve_chat_endpoint_inplace", {"in": base_url, "out": u})
        except Exception:
            pass
        return u
    out = (u if u.endswith("/") else u + "/") + "v1/chat/completions"
    try:
        _dbg("resolve_chat_endpoint", {"in": base_url, "out": out})
    except Exception:
        pass
    return out


_DATA_URL_RE = re.compile(r"data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\r\n]+")
_HTTP_URL_RE = re.compile(r"https?://\S+")


def _clean_url(url_val: str) -> str:
    out = url_val.rstrip(")] .>,\"'")
    try:
        _dbg("clean_url", {"in": url_val[:120], "out": out[:120]})
    except Exception:
        pass
    return out


def _find_media_url(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    try:
        _dbg("find_media_url_enter", {"len": len(text)})
    except Exception:
        pass
    data_match = _DATA_URL_RE.search(text)
    if data_match:
        u = _clean_url(data_match.group(0))
        try:
            _dbg("find_media_url_data", u[:200])
        except Exception:
            pass
        return u
    http_match = _HTTP_URL_RE.search(text)
    if http_match:
        u = _clean_url(http_match.group(0))
        try:
            _dbg("find_media_url_http", u[:200])
        except Exception:
            pass
        return u
    return None


def _search_media_in_obj(obj: Any) -> str | None:
    # Recursively search for image URLs or data URLs in nested structures.
    if isinstance(obj, str):
        r = _find_media_url(obj)
        try:
            if r:
                _dbg("search_media_in_str_found", r[:200])
            else:
                _dbg("search_media_in_str_none", None)
        except Exception:
            pass
        return r
    if isinstance(obj, list):
        try:
            _dbg("search_media_in_list_enter", {"len": len(obj)})
        except Exception:
            pass
        for item in obj:
            url_val = _search_media_in_obj(item)
            if url_val:
                return _clean_url(url_val)
        return None
    if isinstance(obj, dict):
        try:
            _dbg("search_media_in_dict_enter", {"keys": list(obj.keys())[:20]})
        except Exception:
            pass
        url_val = obj.get("url")
        if isinstance(url_val, str):
            media = _find_media_url(url_val) or url_val
            if media:
                return _clean_url(media)
        for key in ("image_url", "text", "content", "parts"):
            if key in obj:
                url_val = _search_media_in_obj(obj[key])
                if url_val:
                    return _clean_url(url_val)
        for value in obj.values():
            url_val = _search_media_in_obj(value)
            if url_val:
                return _clean_url(url_val)
    return None


def _extract_url_from_parts(parts: Iterable[Any]) -> str | None:
    try:
        _dbg("extract_url_from_parts_enter", {"len": len(list(parts)) if hasattr(parts, "__len__") else None})
    except Exception:
        pass
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "image_url":
            image_entry = part.get("image_url")
            if isinstance(image_entry, dict):
                url_val = image_entry.get("url")
                if isinstance(url_val, str):
                    try:
                        _dbg("parts_image_url_dict", url_val[:200])
                    except Exception:
                        pass
                    return _clean_url(url_val)
            if isinstance(image_entry, str):
                try:
                    _dbg("parts_image_url_str", image_entry[:200])
                except Exception:
                    pass
                return _clean_url(image_entry)
        if part.get("type") == "text":
            text = part.get("text")
            url_val = _find_media_url(text)
            if url_val:
                try:
                    _dbg("parts_text_url", url_val[:200])
                except Exception:
                    pass
                return url_val
        url_val = _search_media_in_obj(part)
        if url_val:
            try:
                _dbg("parts_nested_url", url_val[:200])
            except Exception:
                pass
            return _clean_url(url_val)
    return None


def _extract_image_url(message: dict[str, Any]) -> str:
    try:
        _dbg("extract_image_url_enter", {"message_keys": list(message.keys())})
    except Exception:
        pass
    content = message.get("content")
    if isinstance(content, list):
        url_val = _extract_url_from_parts(content)
        if url_val:
            _dbg("extract_from_parts", url_val)
            return _clean_url(url_val)
    if isinstance(content, str):
        url_val = _find_media_url(content)
        if url_val:
            _dbg("extract_from_string", url_val)
            return _clean_url(url_val)
    url_val = _search_media_in_obj(content)
    if url_val:
        _dbg("extract_from_nested", url_val)
        return _clean_url(url_val)
    try:
        _dbg(
            "no_image_url_in_content",
            {
                "message_keys": list(message.keys()),
                "content_type": type(content).__name__ if content is not None else None,
                "content_keys": list(content.keys()) if isinstance(content, dict) else None,
                "content_len": len(content) if isinstance(content, (list, str)) else None,
            },
        )
    except Exception:
        pass
    raise RuntimeError("provider returned no image URL in message content")


def _extract_from_stream(resp: requests.Response) -> Tuple[str | None, list[dict[str, Any]]]:
    try:
        _dbg("stream_enter", {"status": resp.status_code, "headers": dict(resp.headers)})
    except Exception:
        pass
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
                _dbg("stream_text_url", last_url)
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
                    _dbg("stream_parts_url", last_url)
                    break
            if isinstance(content, str):
                url_val = _find_media_url(content)
                if url_val:
                    last_url = url_val
                    _dbg("stream_string_url", last_url)
                    break
            url_val = _search_media_in_obj(content)
            if url_val:
                last_url = url_val
                _dbg("stream_nested_url", last_url)
                break
    _dbg("stream_done", {"last_url": last_url, "chunks": len(chunks)})
    return last_url, chunks


def _build_content(prompt: str, image_url: str | None) -> List[Dict[str, Any]] | str:
    if image_url:
        out = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
        try:
            _dbg("build_content_with_image", {"prompt_len": len(prompt), "image_url": image_url})
        except Exception:
            pass
        return out
    try:
        _dbg("build_content_text_only", {"prompt_len": len(prompt)})
    except Exception:
        pass
    return prompt


def _build_edit_content(prompt: str, images: list[str]) -> List[Dict[str, Any]]:
    parts: list[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    for url in images:
        parts.append({"type": "image_url", "image_url": {"url": url}})
    try:
        _dbg("build_edit_content", {"prompt_len": len(prompt), "images": len(images)})
    except Exception:
        pass
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
    _dbg("images_api_request", {"url": url + "v1/images/generations", "model": payload["model"], "size": size})

    t0 = time.perf_counter()
    response = requests.post(
        f"{url}v1/images/generations",
        headers=_headers(api_key),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    try:
        _dbg("images_api_response", {"status": response.status_code, "duration_ms": int((time.perf_counter() - t0) * 1000)})
    except Exception:
        pass

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
        try:
            _dbg("images_api_no_url", {"data_keys": list(data.keys())})
        except Exception:
            pass
        raise RuntimeError("provider returned no image URL in response")
    _dbg("images_api_result", image_out)
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
    endpoint = _resolve_chat_endpoint(base_url)
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
    _dbg("chat_api_request", {"url": endpoint, "model": payload["model"], "stream": False, "prompt": prompt})
    t0 = time.perf_counter()
    response = requests.post(
        endpoint,
        headers=_headers(api_key),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=120,
    )
    response.raise_for_status()
    try:
        _dbg("chat_api_response", {"status": response.status_code})
    except Exception:
        pass

    provider_response: Dict[str, Any] = {
        "provider": provider_name,
        "model": payload["model"],
        "request": payload,
    }

    data = response.json()
    try:
        _dbg("chat_api_response_text", response.text[:1000])
    except Exception:
        pass
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("provider returned no choices")
    message = choices[0].get("message") or {}
    try:
        _dbg("chat_response_shape", {"choices": len(choices), "message_keys": list(message.keys())})
    except Exception:
        pass
    try:
        image_out = _extract_image_url(message)
    except Exception:
        alt = _search_media_in_obj(data)
        image_out = _clean_url(alt) if isinstance(alt, str) else None

    provider_response["raw"] = data
    try:
        if _debug_enabled():
            h = _headers(api_key)
            sh = {k: ("Bearer ***" if k.lower() == "authorization" else v) for k, v in h.items()}
            dbg = {
                "request": {"method": "POST", "url": endpoint, "headers": sh, "body": payload},
                "response": {"status_code": response.status_code, "headers": dict(response.headers), "text": response.text[:2000]},
                "duration_ms": int((time.perf_counter() - t0) * 1000),
            }
            if isinstance(provider_response["raw"], dict):
                provider_response["raw"]["debug"] = dbg
    except Exception:
        pass
    _dbg("chat_final_url", image_out)
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
    stream: bool | None = None,
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

    endpoint = _resolve_chat_endpoint(base_url)
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
    stream = False
    payload["stream"] = False
    if size:
        payload["size"] = size
    _dbg("chat_edit_request", {"url": endpoint, "model": payload["model"], "images": len(urls), "size": size, "stream": False})

    t0 = time.perf_counter()
    response = requests.post(
        endpoint,
        headers=_headers(api_key),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=120,
        stream=False,
    )
    response.raise_for_status()
    try:
        _dbg("chat_edit_response", {"status": response.status_code, "duration_ms": int((time.perf_counter() - t0) * 1000)})
    except Exception:
        pass
    provider_response: Dict[str, Any] = {
        "provider": provider_name,
        "model": payload["model"],
        "request": payload,
    }

    data = response.json()
    try:
        _dbg("chat_edit_response_text", response.text[:1000])
    except Exception:
        pass
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("provider returned no choices")
    message = choices[0].get("message") or {}
    try:
        image_out = _extract_image_url(message)
    except Exception:
        alt = _search_media_in_obj(data)
        image_out = _clean_url(alt) if isinstance(alt, str) else None

    provider_response["raw"] = data
    try:
        if _debug_enabled():
            h = _headers(api_key)
            sh = {k: ("Bearer ***" if k.lower() == "authorization" else v) for k, v in h.items()}
            dbg = {
                "request": {"method": "POST", "url": endpoint, "headers": sh, "body": payload},
                "response": {"status_code": response.status_code, "headers": dict(response.headers), "text": response.text[:2000]},
            }
            if isinstance(provider_response["raw"], dict):
                provider_response["raw"]["debug"] = dbg
    except Exception:
        pass
    _dbg("chat_edit_final_url", image_out)
    return image_out, provider_response
def _debug_enabled() -> bool:
    try:
        s = get_settings()
        flag_settings = bool(getattr(s, "debug", False))
    except Exception:
        flag_settings = False
    flag_store = False
    try:
        from app.services.store import get_store
        flag_store = bool(get_store().get_debug())
    except Exception:
        flag_store = False
    return bool(flag_settings or flag_store)


def _dbg(label: str, data: Any) -> None:
    if not _debug_enabled():
        return
    try:
        print("[openai_image]", label, ":", data)
    except Exception:
        try:
            print("[openai_image]", label)
        except Exception:
            pass
