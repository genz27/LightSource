from __future__ import annotations

import json
import datetime as dt
from typing import Any, Dict, Tuple, List, Callable
import time
import logging
import requests
import base64
import mimetypes
import re
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

def _parse_model_settings(model: str | None) -> Tuple[str | None, int | None]:
    if not isinstance(model, str):
        return None, None
    m = model.lower()
    orientation = "portrait" if "portrait" in m else "landscape"
    duration = 10 if "10s" in m else (15 if "15s" in m else None)
    return orientation, duration


def create_video(
    prompt: str,
    *,
    model: str,
    image: str | None,
    api_key: str | None,
    base_url: str | None,
    debug: bool = False,
    video: str | None = None,
    role: str | None = None,
    duration_seconds: int | None = None,
    resolution: str | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> Dict[str, Any]:
    url = _normalize_base_url(base_url) + "v1/chat/completions"
    image_send = _to_data_uri(image) if isinstance(image, str) else None
    video_send = _to_data_uri(video) if isinstance(video, str) else None
    content: List[Dict[str, Any]] | str
    if image_send or video_send:
        items: List[Dict[str, Any]] = []
        if isinstance(prompt, str) and prompt.strip():
            items.append({"type": "text", "text": prompt})
        if image_send:
            items.append({"type": "image_url", "image_url": {"url": image_send}})
        if video_send:
            items.append({"type": "video_url", "video_url": {"url": video_send}})
        content = items
    else:
        content = prompt
    payload: Dict[str, Any] = {"model": model, "messages": [{"role": "user", "content": content}], "stream": True}
    h = _headers(api_key)
    sh = {k: ("Bearer ***" if k.lower() == "authorization" else v) for k, v in h.items()}
    t0 = time.perf_counter()
    resp = requests.post(url, headers=h, data=json.dumps(payload), timeout=120, stream=True)
    if resp.status_code not in (200, 201, 202):
        text = None
        try:
            text = resp.text
            data = json.loads(text)
        except Exception:
            data = _error("Invalid JSON response")
        if debug and isinstance(data, dict):
            dbg = {"request": {"method": "POST", "url": url, "headers": sh, "body": payload}, "response": {"status_code": resp.status_code, "headers": dict(resp.headers), "text": (text or "")[:2000]}, "duration_ms": int((time.perf_counter() - t0) * 1000)}
            try:
                logging.getLogger("app.interface.sora2").info(json.dumps({"chat_completions": dbg}))
            except Exception:
                pass
            data["debug"] = dbg
        return data if "error" in data else _error(f"HTTP {resp.status_code}")
    result_url: str | None = None
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        line = raw.strip()
        if not line:
            continue
        if line.startswith("data:"):
            content_str = line[5:].strip()
            if content_str == "[DONE]":
                break
            try:
                obj = json.loads(content_str)
            except Exception:
                m = re.search(r"(https?://\S+|data:video/\w+;base64,[A-Za-z0-9+/=]+)", content_str)
                if m:
                    result_url = m.group(1)
                continue
            try:
                choices = obj.get("choices") or []
                if choices:
                    c0 = choices[0]
                    delta = c0.get("delta") or {}
                    rc = delta.get("reasoning_content")
                    if isinstance(rc, str) and on_progress is not None:
                        try:
                            mm = re.search(r"(\d+(?:\.\d+)?)%", rc)
                            if mm:
                                val = float(mm.group(1))
                                on_progress(val)
                        except Exception:
                            pass
                    msg_content = delta.get("content")
                    if isinstance(msg_content, str):
                        m = re.search(r"src=['\"]\s*(https?://[^'\"\s]+)", msg_content)
                        if not m:
                            m = re.search(r"(https?://\S+|data:video/\w+;base64,[A-Za-z0-9+/=]+)", msg_content)
                        if m:
                            result_url = m.group(1)
                            break
            except Exception:
                pass
    if isinstance(result_url, str) and result_url:
        try:
            b64 = base64.b64encode(result_url.encode("utf-8")).decode("ascii")
            video_id = f"url:{b64}"
        except Exception:
            video_id = str(int(time.perf_counter() * 1000))
    else:
        video_id = str(int(time.perf_counter() * 1000))
    out = {"status": ("succeeded" if result_url else "processing"), "result_url": result_url, "video_url": result_url, "video_id": video_id, "model": model}
    if debug and isinstance(out, dict):
        dbg = {"request": {"method": "POST", "url": url, "headers": sh, "body": payload}, "response": {"status_code": 200, "headers": dict(resp.headers), "text": "[streamed]", "duration_ms": int((time.perf_counter() - t0) * 1000)}}
        try:
            logging.getLogger("app.interface.sora2").info(json.dumps({"chat_completions": dbg}))
        except Exception:
            pass
        out["debug"] = dbg
    return out


def get_video(
    video_id: str,
    *,
    api_key: str | None,
    base_url: str | None,
    debug: bool = False,
) -> Dict[str, Any]:
    h = _headers(api_key)
    sh = {k: ("Bearer ***" if k.lower() == "authorization" else v) for k, v in h.items()}
    t0 = time.perf_counter()
    if isinstance(video_id, str) and video_id.startswith("url:"):
        try:
            b64 = video_id.split(":", 1)[1]
            url_val = base64.b64decode(b64.encode("ascii")).decode("utf-8")
        except Exception:
            url_val = None
        out = {"status": ("succeeded" if url_val else "failed"), "result_url": url_val, "video_url": url_val}
        if debug and isinstance(out, dict):
            dbg = {"request": {"method": "GET", "url": "internal:url", "headers": sh}, "response": {"status_code": 200, "headers": {}, "text": str(out)[:2000]}, "duration_ms": int((time.perf_counter() - t0) * 1000)}
            try:
                logging.getLogger("app.interface.sora2").info(json.dumps({"get_video": dbg}))
            except Exception:
                pass
            out["debug"] = dbg
        return out
    return {"status": "processing", "result_url": None, "video_url": None}


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
    orient_from_model, dur_from_model = _parse_model_settings(model)
    orient_eff = orientation if orientation in ("landscape", "portrait") else orient_from_model
    dur_eff = duration_seconds if isinstance(duration_seconds, int) and duration_seconds > 0 else (dur_from_model or 6)
    res_eff = resolution or ("1024x576" if orient_eff == "landscape" else "576x1024")
    data = create_video(
        prompt,
        model=model,
        image=None,
        api_key=api_key,
        base_url=base_url,
        duration_seconds=dur_eff,
        resolution=res_eff,
    )
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
        "orientation": orient_eff,
        "duration_seconds": dur_eff,
        "resolution": res_eff,
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
    orient_from_model, dur_from_model = _parse_model_settings(model)
    orient_eff = orientation if orientation in ("landscape", "portrait") else orient_from_model
    dur_eff = duration_seconds if isinstance(duration_seconds, int) and duration_seconds > 0 else (dur_from_model or 6)
    res_eff = resolution or ("1024x576" if orient_eff == "landscape" else "576x1024")
    data = create_video(
        prompt,
        model=model,
        image=image_url,
        api_key=api_key,
        base_url=base_url,
        duration_seconds=dur_eff,
        resolution=res_eff,
    )
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
        "orientation": orient_eff,
        "duration_seconds": dur_eff,
        "resolution": res_eff,
        "source_image": image_url,
        "finished_at": dt.datetime.utcnow().isoformat() + "Z",
        "raw": data,
    }
    return video_url, provider_response


def remix_video(
    video_url: str,
    prompt: str,
    *,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    orientation: str | None = None,
    duration_seconds: int = 6,
    resolution: str | None = None,
) -> Tuple[str | None, Dict[str, Any]]:
    orient_from_model, dur_from_model = _parse_model_settings(model)
    orient_eff = orientation if orientation in ("landscape", "portrait") else orient_from_model
    dur_eff = duration_seconds if isinstance(duration_seconds, int) and duration_seconds > 0 else (dur_from_model or 6)
    res_eff = resolution or ("1024x576" if orient_eff == "landscape" else "576x1024")
    data = create_video(
        prompt,
        model=model,
        image=None,
        api_key=api_key,
        base_url=base_url,
        video=video_url,
        duration_seconds=dur_eff,
        resolution=res_eff,
    )
    out_url = data.get("video_url") or data.get("result_url")
    vid = data.get("video_id")
    if not out_url and isinstance(vid, str):
        try:
            detail = get_video(vid, api_key=api_key, base_url=base_url)
            out_url = detail.get("video_url") or detail.get("result_url")
            data = {**data, **detail}
        except Exception:
            pass
    provider_response: Dict[str, Any] = {
        "provider": "sora2",
        "model": model,
        "status": data.get("status") or ("succeeded" if out_url else "processing"),
        "orientation": orient_eff,
        "duration_seconds": dur_eff,
        "resolution": res_eff,
        "source_video": video_url,
        "finished_at": dt.datetime.utcnow().isoformat() + "Z",
        "raw": data,
    }
    return out_url, provider_response


def create_role(
    video_url: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    debug: bool = False,
) -> Dict[str, Any]:
    url = _normalize_base_url(base_url) + "v1/roles"
    video_send = _to_data_uri(video_url) if isinstance(video_url, str) else None
    payload: Dict[str, Any] = {"video": video_send}
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
                logging.getLogger("app.interface.sora2").info(json.dumps({"create_role": dbg}))
            except Exception:
                pass
            if isinstance(data, dict):
                data["debug"] = dbg
        return data if "error" in data else _error(f"HTTP {resp.status_code}")
    if debug and isinstance(data, dict):
        dbg = {
            "request": {"method": "POST", "url": url, "headers": sh, "body": payload},
            "response": {"status_code": resp.status_code, "headers": dict(resp.headers), "text": resp.text[:2000]},
            "duration_ms": int((time.perf_counter() - t0) * 1000),
        }
        try:
            logging.getLogger("app.interface.sora2").info(json.dumps({"create_role": dbg}))
        except Exception:
            pass
        data["debug"] = dbg
    return data


def create_role_and_generate(
    video_url: str,
    prompt: str,
    *,
    model: str,
    api_key: str | None = None,
    base_url: str | None = None,
    orientation: str | None = None,
    duration_seconds: int = 6,
    resolution: str | None = None,
    ) -> Tuple[str | None, Dict[str, Any]]:
    role_data = create_role(video_url, api_key=api_key, base_url=base_url)
    role_name = None
    if isinstance(role_data, dict):
        role_name = role_data.get("role") or role_data.get("role_name") or role_data.get("name")
    orient_from_model, dur_from_model = _parse_model_settings(model)
    orient_eff = orientation if orientation in ("landscape", "portrait") else orient_from_model
    dur_eff = duration_seconds if isinstance(duration_seconds, int) and duration_seconds > 0 else (dur_from_model or 6)
    res_eff = resolution or ("1024x576" if orient_eff == "landscape" else "576x1024")
    data = create_video(
        prompt,
        model=model,
        image=None,
        api_key=api_key,
        base_url=base_url,
        role=role_name,
        duration_seconds=dur_eff,
        resolution=res_eff,
    )
    out_url = data.get("video_url") or data.get("result_url")
    vid = data.get("video_id")
    if not out_url and isinstance(vid, str):
        try:
            detail = get_video(vid, api_key=api_key, base_url=base_url)
            out_url = detail.get("video_url") or detail.get("result_url")
            data = {**data, **detail}
        except Exception:
            pass
    provider_response: Dict[str, Any] = {
        "provider": "sora2",
        "model": model,
        "status": data.get("status") or ("succeeded" if out_url else "processing"),
        "orientation": orient_eff,
        "duration_seconds": dur_eff,
        "resolution": res_eff,
        "role": role_name,
        "source_video": video_url,
        "finished_at": dt.datetime.utcnow().isoformat() + "Z",
        "raw": {"role": role_data, "video": data},
    }
    return out_url, provider_response


def _parse_user_messages(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt_texts: List[str] = []
    image_url: str | None = None
    video_url: str | None = None
    video_from_item = False
    for m in messages:
        if not isinstance(m, dict):
            continue
        if str(m.get("role", "")).lower() != "user":
            continue
        content = m.get("content")
        if isinstance(content, str):
            txt = content.strip()
            prompt_texts.append(txt)
            if not video_url:
                match = re.search(r"(https?://\S+|data:video/\w+;base64,[A-Za-z0-9+/=]+)", txt)
                if match:
                    video_url = match.group(1)
        elif isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                t = item.get("type")
                if t == "text":
                    txt = str(item.get("text") or "").strip()
                    if txt:
                        prompt_texts.append(txt)
                        if not video_url:
                            match = re.search(r"(https?://\S+|data:video/\w+;base64,[A-Za-z0-9+/=]+)", txt)
                            if match:
                                video_url = match.group(1)
                elif t == "image_url":
                    iu = item.get("image_url") or {}
                    u = iu.get("url")
                    if isinstance(u, str):
                        image_url = u
                elif t == "video_url":
                    vu = item.get("video_url") or {}
                    u = vu.get("url")
                    if isinstance(u, str):
                        video_url = u
                        video_from_item = True
    prompt = "\n".join([p for p in prompt_texts if p]) if prompt_texts else None
    return {"prompt": prompt, "image_url": image_url, "video_url": video_url, "video_from_item": video_from_item}


def generate_from_chat_messages(
    model: str,
    messages: List[Dict[str, Any]],
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    orientation: str | None = None,
    duration_seconds: int = 6,
    resolution: str | None = None,
) -> Tuple[str | None, Dict[str, Any]]:
    parsed = _parse_user_messages(messages)
    prompt = parsed.get("prompt")
    image_url = parsed.get("image_url")
    video_url = parsed.get("video_url")
    video_from_item = bool(parsed.get("video_from_item"))
    orient_from_model, dur_from_model = _parse_model_settings(model)
    orient_eff = orientation if orientation in ("landscape", "portrait") else orient_from_model
    dur_eff = duration_seconds if isinstance(duration_seconds, int) and duration_seconds > 0 else (dur_from_model or 6)
    res_eff = resolution or ("1024x576" if orient_eff == "landscape" else "576x1024")
    if video_url and not prompt and video_from_item:
        data = create_role(video_url, api_key=api_key, base_url=base_url)
        provider_response: Dict[str, Any] = {
            "provider": "sora2",
            "model": model,
            "status": data.get("status") or "succeeded",
            "orientation": orient_eff,
            "duration_seconds": dur_eff,
            "resolution": res_eff,
            "role": data.get("role") or data.get("role_name") or data.get("name"),
            "source_video": video_url,
            "finished_at": dt.datetime.utcnow().isoformat() + "Z",
            "raw": data,
        }
        return None, provider_response
    if video_url and prompt:
        if video_from_item:
            return create_role_and_generate(
                video_url,
                prompt,
                model=model,
                api_key=api_key,
                base_url=base_url,
                orientation=orient_eff,
                duration_seconds=dur_eff,
                resolution=res_eff,
            )
        return remix_video(
            video_url,
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            orientation=orient_eff,
            duration_seconds=dur_eff,
            resolution=res_eff,
        )
    if image_url:
        return image_to_video(
            image_url,
            prompt or "",
            model=model,
            api_key=api_key,
            base_url=base_url,
            orientation=orient_eff,
            duration_seconds=dur_eff,
            resolution=res_eff,
        )
    return generate_video(
        prompt or "",
        model=model,
        api_key=api_key,
        base_url=base_url,
        orientation=orient_eff,
        duration_seconds=dur_eff,
        resolution=res_eff,
    )