from __future__ import annotations

import json
import datetime as dt
from typing import Any, Dict, Tuple
import time
import logging
import requests
import base64
import mimetypes
from pathlib import Path
from app.config import get_settings


DEFAULT_BASE_URL = "https://sora2api.airgzn.top/"


def _headers(api_key: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _normalize_base_url(url: str | None) -> str:
    url = url or DEFAULT_BASE_URL
    return url if url.endswith("/") else url + "/"


def _error(message: str) -> Dict[str, Any]:
    return {"error": {"message": message, "type": "client_error", "param": None, "code": None}}


def _to_data_uri(src: str) -> str:
    if src.startswith("data:"):
        return src
    if src.startswith("/media/"):
        settings = get_settings()
        rel = src[len("/media/") :]
        fp = Path(settings.storage_base) / rel
        mime = mimetypes.guess_type(fp.name)[0] or "image/png"
        data = fp.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return src


def create_video(
    prompt: str,
    *,
    model: str,
    image: str | None,
    api_key: str | None,
    base_url: str | None,
    debug: bool = False,
) -> Dict[str, Any]:
    url = _normalize_base_url(base_url) + "v1/videos"
    image_send = _to_data_uri(image) if isinstance(image, str) else None
    payload = {"model": model, "prompt": prompt, "image": image_send}
    h = _headers(api_key)
    sh = {k: ("Bearer ***" if k.lower() == "authorization" else v) for k, v in h.items()}
    t0 = time.perf_counter()
    resp = requests.post(url, headers=h, data=json.dumps(payload), timeout=30)
    try:
        data = resp.json()
    except Exception:
        data = _error("Invalid JSON response")
    if resp.status_code not in (200, 201, 202):
        if debug and isinstance(data, dict):
            dbg = {
                "request": {"method": "POST", "url": url, "headers": sh, "body": payload},
                "response": {"status_code": resp.status_code, "headers": dict(resp.headers), "text": resp.text[:2000]},
                "duration_ms": int((time.perf_counter() - t0) * 1000),
            }
            try:
                logging.getLogger("app.interface.sora2").info(json.dumps({"create_video": dbg}))
            except Exception:
                pass
            data["debug"] = dbg
        return data if "error" in data else _error(f"HTTP {resp.status_code}")
    if debug and isinstance(data, dict):
        dbg = {
            "request": {"method": "POST", "url": url, "headers": sh, "body": payload},
            "response": {"status_code": resp.status_code, "headers": dict(resp.headers), "text": resp.text[:2000]},
            "duration_ms": int((time.perf_counter() - t0) * 1000),
        }
        try:
            logging.getLogger("app.interface.sora2").info(json.dumps({"create_video": dbg}))
        except Exception:
            pass
        data["debug"] = dbg
    return data


def get_video(
    video_id: str,
    *,
    api_key: str | None,
    base_url: str | None,
    debug: bool = False,
) -> Dict[str, Any]:
    url = _normalize_base_url(base_url) + f"v1/videos/{video_id}"
    h = _headers(api_key)
    sh = {k: ("Bearer ***" if k.lower() == "authorization" else v) for k, v in h.items()}
    t0 = time.perf_counter()
    resp = requests.get(url, headers=h, timeout=30)
    try:
        data = resp.json()
    except Exception:
        data = _error("Invalid JSON response")
    if resp.status_code != 200:
        if isinstance(data, dict) and data.get("detail"):
            return {"error": {"message": data.get("detail"), "type": "provider_error", "param": None, "code": resp.status_code}}
        return data if "error" in data else _error(f"HTTP {resp.status_code}")
    # 兼容字段：如果 result_url 存在但 video_url 为空，则补充同值
    if isinstance(data, dict) and data.get("result_url") and not data.get("video_url"):
        data["video_url"] = data.get("result_url")
    if debug and isinstance(data, dict):
        dbg = {
            "request": {"method": "GET", "url": url, "headers": sh},
            "response": {"status_code": resp.status_code, "headers": dict(resp.headers), "text": resp.text[:2000]},
            "duration_ms": int((time.perf_counter() - t0) * 1000),
        }
        try:
            logging.getLogger("app.interface.sora2").info(json.dumps({"get_video": dbg}))
        except Exception:
            pass
        data["debug"] = dbg
    return data


# 保留原有占位方法，便于无外部服务时的演示
def generate_video(
    prompt: str,
    *,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    orientation: str | None = None,
    duration_seconds: int = 6,
    resolution: str | None = None,
) -> Tuple[str | None, Dict[str, Any]]:
    model_to_send = model
    if orientation in ("landscape", "portrait"):
        model_to_send = f"sora-video-{orientation}"
    data = create_video(prompt, model=model_to_send, image=None, api_key=api_key, base_url=base_url)
    video_url = data.get("video_url") or data.get("result_url")
    video_id = data.get("video_id")
    if not video_url and isinstance(video_id, str):
        # 尝试一次查询详情以获取最终 URL
        try:
            detail = get_video(video_id, api_key=api_key, base_url=base_url)
            video_url = detail.get("video_url") or detail.get("result_url")
            data = {**data, **detail}
        except Exception:
            pass
    provider_response: Dict[str, Any] = {
        "provider": "sora2",
        "model": model,
        "status": data.get("status") or ("succeeded" if video_url else "processing"),
        "orientation": orientation,
        "duration_seconds": duration_seconds,
        "resolution": resolution,
        "finished_at": dt.datetime.utcnow().isoformat() + "Z",
        "raw": data,
    }
    return video_url, provider_response


def image_to_video(
    image_url: str,
    prompt: str,
    *,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    orientation: str | None = None,
    duration_seconds: int = 6,
    resolution: str | None = None,
) -> Tuple[str | None, Dict[str, Any]]:
    model_to_send = model
    if orientation in ("landscape", "portrait"):
        model_to_send = f"sora-video-{orientation}"
    data = create_video(prompt, model=model_to_send, image=image_url, api_key=api_key, base_url=base_url)
    video_url = data.get("video_url") or data.get("result_url")
    video_id = data.get("video_id")
    if not video_url and isinstance(video_id, str):
        try:
            detail = get_video(video_id, api_key=api_key, base_url=base_url)
            video_url = detail.get("video_url") or detail.get("result_url")
            data = {**data, **detail}
        except Exception:
            pass
    provider_response: Dict[str, Any] = {
        "provider": "sora2",
        "model": model,
        "status": data.get("status") or ("succeeded" if video_url else "processing"),
        "orientation": orientation,
        "duration_seconds": duration_seconds,
        "resolution": resolution,
        "source_image": image_url,
        "finished_at": dt.datetime.utcnow().isoformat() + "Z",
        "raw": data,
    }
    return video_url, provider_response