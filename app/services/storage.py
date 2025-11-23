from __future__ import annotations

import os
import base64
import re
from pathlib import Path
from typing import Optional
from app.schemas import AssetOut

from fastapi import HTTPException, UploadFile, status

from app.config import get_settings


def ensure_storage_dir(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)


_DATA_URL_RE = re.compile(r"^data:image/([a-zA-Z0-9.+-]+);base64,(.+)$", re.DOTALL)


def save_data_url_image(job_id: str, data_url: str, *, filename: str = "output") -> str:
    """Persist a data URL image to storage and return the static media URL."""

    match = _DATA_URL_RE.match((data_url or "").strip())
    if not match:
        raise ValueError("invalid data url")

    mime = match.group(1).lower()
    b64_payload = match.group(2).strip()
    payload = base64.b64decode(b64_payload)

    ext = "png"
    if "jpeg" in mime or mime == "jpg":
        ext = "jpg"
    elif "gif" in mime:
        ext = "gif"
    elif "webp" in mime:
        ext = "webp"
    elif "bmp" in mime:
        ext = "bmp"
    elif "tiff" in mime:
        ext = "tiff"

    settings = get_settings()
    base = Path(settings.storage_base)
    ensure_storage_dir(base / job_id)
    dest = base / job_id / f"{filename}.{ext}"
    with dest.open("wb") as f:
        f.write(payload)

    rel_path = f"{job_id}/{filename}.{ext}"
    return f"/media/{rel_path}"


def _validate_image_upload(upload: UploadFile, max_bytes: int) -> bytes:
    allowed_types = {"image/png", "image/jpeg", "image/webp"}
    if upload.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type",
        )
    data = upload.file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image too large",
        )
    return data


def save_source_image(job_id: str, upload: UploadFile, max_bytes: int = 5 * 1024 * 1024) -> tuple[str, str]:
    """Persist uploaded source image to storage and return (relative_path, public_url)."""

    settings = get_settings()
    base = Path(settings.storage_base)
    ensure_storage_dir(base / job_id)
    ext = Path(upload.filename or "source").suffix or ".png"
    filename = f"source{ext}"
    dest = base / job_id / filename
    data = _validate_image_upload(upload, max_bytes)
    with dest.open("wb") as f:
        f.write(data)
    # public url served via StaticFiles mount
    rel_path = f"{job_id}/{filename}"
    url = f"/media/{rel_path}"
    return rel_path, url


def placeholder_output(kind: str, job_id: str) -> tuple[str, str]:
    """Produce placeholder output file path/url for assets."""

    settings = get_settings()
    base = Path(settings.storage_base)
    ensure_storage_dir(base / job_id)
    ext = ".png" if kind == "text_to_image" else ".mp4"
    filename = f"output{ext}"
    dest = base / job_id / filename
    if not dest.exists():
        dest.write_bytes(b"")  # placeholder empty file
    rel_path = f"{job_id}/{filename}"
    url = f"/media/{rel_path}"
    return rel_path, url


def delete_asset_files(asset: AssetOut) -> None:
    try:
        url = asset.url
        if not url.startswith("/media/"):
            return
        rel = url[len("/media/"):]
        job_id = rel.split("/", 1)[0]
        settings = get_settings()
        base = Path(settings.storage_base)
        target = base / job_id
        if target.exists() and target.is_dir():
            for p in target.glob("**/*"):
                try:
                    p.unlink()
                except Exception:
                    pass
            try:
                target.rmdir()
            except Exception:
                pass
    except Exception:
        pass
