from __future__ import annotations

import datetime as dt
from typing import Dict, Tuple

from app.schemas import JobStatus


class Metrics:
    def __init__(self) -> None:
        self.transitions: Dict[Tuple[str, str], int] = {}
        self.started_at: Dict[str, dt.datetime] = {}
        self.durations_sec: list[float] = []
        self.requests_total: int = 0
        self.rate_limited_total: int = 0

    def record_transition(self, old: JobStatus, new: JobStatus) -> None:
        key = (old.value, new.value)
        self.transitions[key] = self.transitions.get(key, 0) + 1

    def mark_started(self, job_id: str) -> None:
        self.started_at[job_id] = dt.datetime.utcnow()

    def mark_finished(self, job_id: str) -> None:
        start = self.started_at.pop(job_id, None)
        if start:
            delta = dt.datetime.utcnow() - start
            self.durations_sec.append(delta.total_seconds())

    def snapshot(self) -> dict:
        count = len(self.durations_sec)
        avg = (sum(self.durations_sec) / count) if count else 0.0
        return {
            "transitions": {f"{a}->{b}": v for (a, b), v in self.transitions.items()},
            "durations_count": count,
            "avg_duration_sec": avg,
            "running": len(self.started_at),
            "requests_total": self.requests_total,
            "rate_limited_total": self.rate_limited_total,
        }


metrics = Metrics()