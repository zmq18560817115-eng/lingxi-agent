"""最小持久化：按 requirement_id 存 JSON 文件。

刻意选 JSON 文件而非数据库——D1 目标是"刷新不丢、能走通"，不是抗并发。
接口（get/save/save_artifact/artifact_path）保持稳定，日后换 SQLite/PG 不影响调用方。
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("LINGXI_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def _path(requirement_id: str) -> Path:
    return DATA_DIR / f"{requirement_id}.json"


def save(requirement_id: str, payload: dict[str, Any]) -> None:
    _path(requirement_id).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get(requirement_id: str) -> dict[str, Any] | None:
    p = _path(requirement_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def update(requirement_id: str, **fields: Any) -> dict[str, Any]:
    payload = get(requirement_id) or {}
    payload.update(fields)
    save(requirement_id, payload)
    return payload


def artifact_dir(requirement_id: str) -> Path:
    d = DATA_DIR / requirement_id
    d.mkdir(parents=True, exist_ok=True)
    return d
