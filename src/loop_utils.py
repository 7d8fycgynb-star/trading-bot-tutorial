"""Pomůcky pro dlouhodobý běh (např. 2denní test)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunLogger:
    """Píše stdout i do souboru."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str) -> None:
        line = f"[{now_iso()}] {message}"
        print(line, flush=True)
        if self.path:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")


def save_state(path: str | Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_state(path: str | Path) -> dict | None:
    path = Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_duration_seconds(
    *,
    days: float | None = None,
    hours: float | None = None,
    minutes: float | None = None,
) -> float | None:
    total = 0.0
    if days:
        total += days * 86400
    if hours:
        total += hours * 3600
    if minutes:
        total += minutes * 60
    return total or None
