from __future__ import annotations

from typing import Protocol

from app.schemas import JobCreate, JobOut


class Provider(Protocol):
    async def generate(self, request: JobCreate, job: JobOut) -> None:
        """Kick off generation for a job. Implementations may be synchronous or async."""
        ...
