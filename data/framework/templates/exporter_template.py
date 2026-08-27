"""
Custom Exporter Template
==========================
Copy here only if none of the built-in exporters (Excel/CSV/JSON/XML) meet your needs.
Implement BaseExporter — the pipeline accepts any exporter interchangeably.
"""
from __future__ import annotations

from pathlib import Path

from core.exporter import BaseExporter
from models.product import Product


class CustomExporter(BaseExporter):
    """
    Template for a custom export format.
    Replace the body of export() with your format-specific logic.
    """

    FILE_EXTENSION = "txt"  # TODO: set your format's extension

    def export(self, products: list[Product], destination: Path) -> Path:
        destination.mkdir(parents=True, exist_ok=True)
        out = destination / f"products.{self.FILE_EXTENSION}"

        with out.open("w", encoding="utf-8") as f:
            for product in products:
                # TODO: write product in your custom format
                f.write(f"{product.sku}\t{product.name}\n")

        return out
