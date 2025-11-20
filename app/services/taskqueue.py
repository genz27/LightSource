from __future__ import annotations

import asyncio
from typing import Optional

from app.schemas import JobOut
from app.services.store import MemoryStore
from app.services.generation import simulate_generation


class TaskQueue:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self._store_ref: Optional[MemoryStore] = None

    async def start(self, store: MemoryStore) -> None:
        self._store_ref = store
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker(store))

    async def enqueue(self, job_id: str) -> None:
        # Ensure worker started even if startup event was skipped
        if self.worker_task is None or self.worker_task.done():
            try:
                if self._store_ref is None:
                    from app.services.store import get_store
                    self._store_ref = get_store()
                self.worker_task = asyncio.create_task(self._worker(self._store_ref))
            except Exception:
                pass
        await self.queue.put(job_id)

    async def _worker(self, store: MemoryStore) -> None:
        while True:
            job_id = await self.queue.get()
            job = store.get_job(job_id)
            if job is None:
                try:
                    from app.db import SessionLocal
                    from app.services.persistence import get_job_db
                    async with SessionLocal() as session:
                        db_job = await get_job_db(session, job_id)
                    if db_job:
                        store.jobs[job_id] = db_job
                        job = db_job
                except Exception:
                    job = None
            if job:
                await simulate_generation(job=job, store=store, source_image_name=None)
            self.queue.task_done()


task_queue = TaskQueue()


def get_task_queue() -> TaskQueue:
    return task_queue