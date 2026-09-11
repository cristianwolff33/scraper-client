from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.exporter import BaseExporter
from models.product import Product


class JsonExporter(BaseExporter):
    """Exports products to a single JSON file. Interchangeable with all other exporters."""

    def export(self, products: list[Product], destination: Path) -> Path:
        destination.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = destination / f"products_{ts}.json"

        data = [p.to_dict() for p in products]
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        return out
