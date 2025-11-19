from __future__ import annotations

import json
import time
from typing import Any, Dict, Tuple
import base64
import mimetypes
from pathlib import Path

import requests


DEFAULT_BASE_URL = "https://api-inference.modelscope.cn/"

# Map internal model codes used in this project to ModelScope model IDs.
MODEL_MAP: dict[str, str] = {
    "qwen-image": "Qwen/Qwen-Image",
    "qwen-image-edit": "Qwen/Qwen-Image-Edit-2509",
}


def _common_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _wait_for_task(
    *,
    task_id: str,
    api_key: str,
    base_url: str,
    task_type: str = "image_generation",
    poll_interval: int = 5,
) -> Dict[str, Any]:
    """Poll ModelScope task API until it succeeds or fails."""

    headers = {**_common_headers(api_key), "X-ModelScope-Task-Type": task_type}
    while True:
        response = requests.get(f"{base_url}v1/tasks/{task_id}", headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        status = data.get("task_status")

        if status == "SUCCEED":
            return data
        if status == "FAILED":
            raise RuntimeError(f"Qwen task failed: {data}")

        time.sleep(poll_interval)


def generate_image(
    prompt: str,
    *,
    model: str,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    size: str | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """Text-to-image generation with Qwen via ModelScope.

    Parameters:
        prompt: 用户提示词。
        model: 内部模型编码（例如 'qwen-image'），会映射到真实的 ModelScope ID。
        api_key: 从渠道配置（providers.api_token）读取的 token。
        base_url: 渠道配置中的 base_url，默认指向 ModelScope 公共推理服务。

    Returns:
        (image_url, provider_response)
        - image_url: 生成图片的可访问 URL（ModelScope 提供）。
        - provider_response: 精简后的 provider 响应（包含 task_id、原始 JSON 等），
          可写入 Job/Asset 的 meta 作为审计信息。
    """

    real_model = MODEL_MAP.get(model, model)
    key = api_key
    url = base_url or DEFAULT_BASE_URL
    if not url.endswith("/"):
        url = url + "/"

    headers = {**_common_headers(key), "X-ModelScope-Async-Mode": "true"}

    payload = {
        "model": real_model,
        "prompt": prompt,
    }
    if size:
        payload["size"] = size
    response = requests.post(
        f"{url}v1/images/generations",
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    task = response.json()
    task_id = task["task_id"]

    data = _wait_for_task(task_id=task_id, api_key=key, base_url=url)
    output_images = data.get("output_images") or []
    if not output_images:
        raise RuntimeError(f"Qwen task succeeded but no output_images: {data}")
    image_url = output_images[0]

    provider_response: Dict[str, Any] = {
        "provider": "qwen",
        "model": real_model,
        "task_id": task_id,
        "task_status": data.get("task_status"),
        "request": payload,
        "raw": data,
    }
    return image_url, provider_response


def edit_image(
    image_url: list[str] | str,
    prompt: str,
    *,
    model: str,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    size: str | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """Image-edit generation with Qwen via ModelScope.

    Parameters:
        image_url: 源图的可访问 URL。
        prompt: 编辑说明。
        model: 内部模型编码（例如 'qwen-image-edit'），会映射到真实 ModelScope ID。
        api_key/base_url: 渠道配置。

    Returns:
        (result_image_url, provider_response)
    """

    real_model = MODEL_MAP.get(model, model)
    key = api_key
    url = base_url or DEFAULT_BASE_URL
    if not url.endswith("/"):
        url = url + "/"

    headers = {**_common_headers(key), "X-ModelScope-Async-Mode": "true"}

    urls: list[str]
    if isinstance(image_url, list):
        urls = image_url
    else:
        urls = [image_url]
    for u in urls:
        if not (isinstance(u, str) and (u.startswith("http://") or u.startswith("https://"))):
            raise RuntimeError("image_url must be http/https URL for Qwen-Image-Edit")

    payload = {
        "model": real_model,
        "prompt": prompt,
        "image_url": urls,
    }
    if size:
        payload["size"] = size
    response = requests.post(
        f"{url}v1/images/generations",
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    task = response.json()
    task_id = task["task_id"]

    data = _wait_for_task(task_id=task_id, api_key=key, base_url=url)
    output_images = data.get("output_images") or []
    if not output_images:
        raise RuntimeError(f"Qwen edit task succeeded but no output_images: {data}")
    result_image_url = output_images[0]

    provider_response: Dict[str, Any] = {
        "provider": "qwen",
        "model": real_model,
        "task_id": task_id,
        "task_status": data.get("task_status"),
        "raw": data,
    }
    return result_image_url, provider_response

