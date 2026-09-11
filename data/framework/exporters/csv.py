from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.exporter import BaseExporter
from models.product import Product


_COLUMNS = [
    "sku", "ean", "name", "brand", "category",
    "description", "price", "currency", "stock",
    "image_urls", "downloaded_images",
]


class CsvExporter(BaseExporter):
    """Exports products to a UTF-8-BOM CSV (compatible with Excel without import wizard)."""

    def export(self, products: list[Product], destination: Path) -> Path:
        destination.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = destination / f"products_{ts}.csv"
        rows = [_flatten_product(product) for product in products]
        fieldnames = _fieldnames(rows)

        with out.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        return out


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    extras: set[str] = set()
    for row in rows:
        extras.update(row)
    return _COLUMNS + sorted(extras.difference(_COLUMNS))


def _flatten_product(product: Product) -> dict[str, Any]:
    row = product.to_dict()
    parameters = row.pop("parameters", {}) or {}
    attributes = row.pop("attributes", {}) or {}
    metadata = row.pop("metadata", {}) or {}
    export_image_urls = _export_image_urls(product, metadata)

    row["image_urls"] = "|".join(export_image_urls)
    row["downloaded_images"] = "|".join(product.downloaded_images)
    row["parameters_json"] = _json(parameters)
    row["attributes_json"] = _json(attributes)
    row["metadata_json"] = _json(metadata)

    if export_image_urls:
        row.setdefault("image_url_1", export_image_urls[0])
        for index, url in enumerate(export_image_urls, start=1):
            row.setdefault(f"zdj{index}", url)

    for source in (parameters, metadata):
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            clean_key = str(key).strip()
            if clean_key and clean_key not in row:
                row[clean_key] = _serialize(value)

    return {key: _serialize(value) for key, value in row.items()}


def _export_image_urls(product: Product, metadata: dict[str, Any]) -> list[str]:
    public_urls = metadata.get("public_image_urls")
    if isinstance(public_urls, list):
        urls = [str(url) for url in public_urls if url]
        if urls:
            return urls
    return product.image_urls


def _serialize(value: Any) -> Any:
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if isinstance(value, dict):
        return _json(value)
    return value


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str) if value else ""
