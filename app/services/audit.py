from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "audit.log"


def write(event: str, payload: Dict[str, Any]) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        line = json.dumps({"event": event, **payload}, ensure_ascii=False)
        LOG_FILE.open("a", encoding="utf-8").write(line + "\n")
    except Exception:
        pass


def read(event: str | None = None, since: float | None = None, until: float | None = None, offset: int = 0, limit: int | None = None) -> list[Dict[str, Any]]:
    items: list[Dict[str, Any]] = []
    try:
        if not LOG_FILE.exists():
            return []
        with LOG_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if event and obj.get("event") != event:
                    continue
                ts = obj.get("ts") or None
                if isinstance(ts, (int, float)):
                    if since is not None and ts < since:
                        continue
                    if until is not None and ts > until:
                        continue
                items.append(obj)
        if offset:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]
    except Exception:
        pass
    return items