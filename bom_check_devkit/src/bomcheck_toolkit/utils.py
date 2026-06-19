from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_json(path: str | Path, data: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_refdes(ref: str) -> str:
    return re.sub(r"\s+", "", str(ref).strip().upper())


def normalize_text_for_compare(text: str) -> str:
    t = str(text).upper().replace("µ", "U")
    t = t.replace("OHM", "R")
    t = re.sub(r"\s+", "", t)
    return t


def contains_any(text: str, keywords: list[str]) -> bool:
    upper = str(text).upper()
    for keyword in keywords:
        key = str(keyword).strip().upper()
        if not key:
            continue
        if re.fullmatch(r"[A-Z0-9_ ]+", key):
            if re.search(rf"(?<![A-Z0-9_]){re.escape(key)}(?![A-Z0-9_])", upper):
                return True
        elif key in upper:
            return True
    return False
