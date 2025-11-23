from __future__ import annotations

from typing import Any, Tuple

from app.interface import flux as flux_client
from app.interface import majicflus as majicflus_client
from app.interface import nano_banana as nano_banana_client
from app.interface import openai_image as openai_image_client
from app.interface import qwen as qwen_client
from app.interface import sora2 as sora2_client
from app.interface import sora_image as sora_image_client


class QwenAdapter:
    def generate_image(self, prompt: str, *, model: str, api_key: str, base_url: str, size: str | None = None) -> Tuple[str, dict]:
        return qwen_client.generate_image(prompt, model=model, api_key=api_key, base_url=base_url, size=size)

    def edit_image(
        self, image_url: list[str] | str, prompt: str, *, model: str, api_key: str, base_url: str, size: str | None = None
    ) -> Tuple[str, dict]:
        return qwen_client.edit_image(image_url, prompt, model=model, api_key=api_key, base_url=base_url, size=size)


class FluxAdapter:
    def generate_image(self, prompt: str, *, model: str, api_key: str, base_url: str, size: str | None = None) -> Tuple[str, dict]:
        return flux_client.generate_image(prompt, api_key=api_key, base_url=base_url, size=size)


class MajicFlusAdapter:
    def generate_image(self, prompt: str, *, model: str, api_key: str, base_url: str, size: str | None = None) -> Tuple[str, dict]:
        return majicflus_client.generate_image(prompt, api_key=api_key, base_url=base_url, size=size)


class NanoBananaAdapter:
    def generate_image(
        self,
        prompt: str,
        *,
        model: str,
        api_key: str | None,
        base_url: str,
        size: str | None = None,
        image_url: str | None = None,
    ) -> Tuple[str, dict]:
        return nano_banana_client.generate_image(
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            size=size,
            image_url=image_url,
        )


class OpenAIImageAdapter:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def generate_image(
        self,
        prompt: str,
        *,
        model: str,
        api_key: str | None,
        base_url: str,
        size: str | None = None,
        image_url: str | None = None,
        api_style: str | None = None,
    ) -> Tuple[str, dict]:
        return openai_image_client.generate_image(
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            size=size,
            image_url=image_url,
            provider_name=self.provider_name,
            api_style=api_style,
        )

    def edit_image(
        self,
        image_url: list[str] | str,
        prompt: str,
        *,
        model: str,
        api_key: str | None,
        base_url: str,
        size: str | None = None,
        api_style: str | None = None,
    ) -> Tuple[str, dict]:
        return openai_image_client.edit_image(
            image_url,
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            size=size,
            provider_name=self.provider_name,
            api_style=api_style,
        )


class SoraImageAdapter:
    def generate_image(
        self,
        prompt: str,
        *,
        model: str,
        api_key: str | None,
        base_url: str,
        size: str | None = None,
        image_url: str | None = None,
    ) -> Tuple[str, dict]:
        return sora_image_client.generate_image(
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            size=size,
            image_url=image_url,
        )


class Sora2Adapter:
    def create_video(
        self,
        prompt: str,
        *,
        model: str,
        image: str | None,
        api_key: str | None,
        base_url: str | None,
        debug: bool | None = None,
        duration_seconds: int | None = None,
        resolution: str | None = None,
        on_progress: Any | None = None,
    ) -> dict:
        return sora2_client.create_video(
            prompt,
            model=model,
            image=image,
            api_key=api_key,
            base_url=base_url,
            debug=bool(debug),
            duration_seconds=duration_seconds,
            resolution=resolution,
            on_progress=on_progress,
        )

    def get_video(
        self,
        video_id: str,
        *,
        api_key: str | None,
        base_url: str | None,
        debug: bool | None = None,
    ) -> dict:
        return sora2_client.get_video(video_id, api_key=api_key, base_url=base_url, debug=bool(debug))

    def generate_video(
        self,
        prompt: str,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        orientation: str | None,
        duration_seconds: int,
        resolution: str | None,
    ) -> Tuple[str | None, dict]:
        return sora2_client.generate_video(
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            orientation=orientation,
            duration_seconds=duration_seconds,
            resolution=resolution,
        )

    def image_to_video(
        self,
        image_url: str,
        prompt: str,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        orientation: str | None,
        duration_seconds: int,
        resolution: str | None,
    ) -> Tuple[str | None, dict]:
        return sora2_client.image_to_video(
            image_url,
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            orientation=orientation,
            duration_seconds=duration_seconds,
            resolution=resolution,
        )

    def remix_video(
        self,
        video_url: str,
        prompt: str,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        orientation: str | None,
        duration_seconds: int,
        resolution: str | None,
    ) -> Tuple[str | None, dict]:
        return sora2_client.remix_video(
            video_url,
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            orientation=orientation,
            duration_seconds=duration_seconds,
            resolution=resolution,
        )

    def create_role(self, video_url: str, *, api_key: str | None, base_url: str | None, debug: bool | None = None) -> dict:
        return sora2_client.create_role(video_url, api_key=api_key, base_url=base_url, debug=bool(debug))

    def create_role_and_generate(
        self,
        video_url: str,
        prompt: str,
        *,
        model: str,
        api_key: str | None,
        base_url: str | None,
        orientation: str | None,
        duration_seconds: int,
        resolution: str | None,
    ) -> Tuple[str | None, dict]:
        return sora2_client.create_role_and_generate(
            video_url,
            prompt,
            model=model,
            api_key=api_key,
            base_url=base_url,
            orientation=orientation,
            duration_seconds=duration_seconds,
            resolution=resolution,
        )

    def generate_from_chat_messages(
        self,
        model: str,
        messages: list[dict],
        *,
        api_key: str | None,
        base_url: str | None,
        orientation: str | None,
        duration_seconds: int,
        resolution: str | None,
    ) -> Tuple[str | None, dict]:
        return sora2_client.generate_from_chat_messages(
            model,
            messages,
            api_key=api_key,
            base_url=base_url,
            orientation=orientation,
            duration_seconds=duration_seconds,
            resolution=resolution,
        )


def resolve_adapter(provider) -> Any | None:
    if not provider:
        return None

    name = provider.name
    capabilities = {c.lower() for c in (provider.capabilities or [])}

    if name == "qwen":
        return QwenAdapter()
    if name == "sora2":
        return Sora2Adapter()
    if name == "sora":
        return SoraImageAdapter()
    if name == "flux":
        return FluxAdapter()
    if name == "majicflus":
        return MajicFlusAdapter()
    if name == "nano-banana-2":
        return NanoBananaAdapter()
    if "image" in capabilities or "image-edit" in capabilities or "edit_image" in capabilities:
        return OpenAIImageAdapter(name)
    return None
