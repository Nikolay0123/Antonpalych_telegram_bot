from pathlib import Path
from functools import lru_cache
from typing import Any, Dict

import json


LANG_DIR = Path(__file__).parent


@lru_cache(maxsize=16)
def load_language(lang_code: str) -> Dict[str, Any]:
    filename = {
        "ru": "ru.json",
        "en": "en.json",
        "zh": "zh.json",
    }.get(lang_code, "ru.json")
    path = LANG_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def t(lang_code: str, key: str, **kwargs: Any) -> str:
    data = load_language(lang_code)
    parts = key.split(".")
    value: Any = data
    for p in parts:
        value = value.get(p, {})
    if not isinstance(value, str):
        return key
    if kwargs:
        return value.format(**kwargs)
    return value

