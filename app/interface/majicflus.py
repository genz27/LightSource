from __future__ import annotations

import json
import time
from typing import Any, Dict, Tuple

import requests


DEFAULT_BASE_URL = "https://api-inference.modelscope.cn/"
MODEL_ID = "MAILAND/majicflus_v1"


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _wait(task_id: str, api_key: str, base_url: str, task_type: str = "image_generation", poll_interval: int = 5) -> Dict[str, Any]:
    h = {**_headers(api_key), "X-ModelScope-Task-Type": task_type}
    while True:
        r = requests.get(f"{base_url}v1/tasks/{task_id}", headers=h, timeout=30)
        r.raise_for_status()
        data = r.json()
        s = data.get("task_status")
        if s == "SUCCEED":
            return data
        if s == "FAILED":
            raise RuntimeError(str(data))
        time.sleep(poll_interval)


def generate_image(prompt: str, *, api_key: str, base_url: str = DEFAULT_BASE_URL, size: str | None = None) -> Tuple[str, Dict[str, Any]]:
    url = base_url or DEFAULT_BASE_URL
    if not url.endswith("/"):
        url = url + "/"
    headers = {**_headers(api_key), "X-ModelScope-Async-Mode": "true"}
    payload: Dict[str, Any] = {"model": MODEL_ID, "prompt": prompt}
    if size:
        payload["size"] = size
    resp = requests.post(f"{url}v1/images/generations", headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), timeout=60)
    resp.raise_for_status()
    task_id = resp.json()["task_id"]
    data = _wait(task_id, api_key, url)
    outs = data.get("output_images") or []
    if not outs:
        raise RuntimeError("no output_images")
    image_url = outs[0]
    provider_response: Dict[str, Any] = {
        "provider": "majicflus",
        "model": MODEL_ID,
        "task_id": task_id,
        "task_status": data.get("task_status"),
        "request": payload,
        "raw": data,
    }
    return image_url, provider_response