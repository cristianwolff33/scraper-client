from __future__ import annotations

import hashlib
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any


def slugify(text: str) -> str:
    """Convert arbitrary text to a filesystem-safe slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s\-]", "", text).strip().lower()
    return re.sub(r"[\s_]+", "-", text)


def clean_text(text: str) -> str:
    """Strip HTML tags, normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_price(raw: str | float | int | None) -> Decimal | None:
    """Safely parse a price from any reasonable input."""
    if raw is None:
        return None
    cleaned = re.sub(r"[^\d.,]", "", str(raw)).replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def flatten_dict(d: dict[str, Any], sep: str = ".", prefix: str = "") -> dict[str, Any]:
    """Recursively flatten a nested dictionary."""
    result: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}{sep}{k}" if prefix else k
        if isinstance(v, dict):
            result.update(flatten_dict(v, sep=sep, prefix=key))
        else:
            result[key] = v
    return result


def deduplicate(items: list[Any], key: str = "sku") -> list[Any]:
    """Remove duplicates by a given attribute or dict key, preserving order."""
    seen: set[Any] = set()
    out = []
    for item in items:
        val = getattr(item, key, None) or (item.get(key) if isinstance(item, dict) else None)
        if val not in seen:
            seen.add(val)
            out.append(item)
    return out


def chunk(lst: list[Any], size: int) -> list[list[Any]]:
    return [lst[i : i + size] for i in range(0, len(lst), size)]
