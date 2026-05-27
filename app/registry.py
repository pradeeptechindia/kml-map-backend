import json
import os
from pathlib import Path

DATA_DIR = Path(os.environ["KML_MAP_DATA_DIR"])
REGISTRY_PATH = DATA_DIR / "registry.json"


def _ensure():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text("[]", encoding="utf-8")


def read() -> list[dict]:
    _ensure()
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _write(entries: list[dict]):
    _ensure()
    REGISTRY_PATH.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def add(entry: dict) -> dict:
    entries = read()
    entries.append(entry)
    _write(entries)
    return entry


def get(cog_id: str) -> dict | None:
    for e in read():
        if e["id"] == cog_id:
            return e
    return None


def remove(cog_id: str) -> dict | None:
    entries = read()
    removed = None
    kept = []
    for e in entries:
        if e["id"] == cog_id:
            removed = e
        else:
            kept.append(e)
    if removed is None:
        return None
    _write(kept)
    return removed