"""
CSV File Adapter Template
==========================
Copy to: adapters/<source_name>/adapter.py
Use for CSV/TSV data exports or supplier price lists.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterator

from adapters.base_adapter import AdapterMode, BaseAdapter
from core.cache import Cache
from core.config import Settings


class CsvFileAdapter(BaseAdapter):
    """
    Adapter for a CSV file data source.
    Reads rows and yields raw dicts — column mapping happens here,
    full normalization in the transformer.
    """

    MODE = AdapterMode.CSV_FILE
    SOURCE_NAME = "csv_example"

    # TODO: set actual path or make it a constructor parameter
    CSV_PATH: Path = Path("data/products.csv")
    DELIMITER: str = ";"
    ENCODING: str = "utf-8-sig"  # handles BOM from Windows Excel exports

    # TODO: map CSV column names → standard raw dict keys
    COLUMN_MAP: dict[str, str] = {
        "Product ID": "sku",
        "Product Name": "name",
        "EAN": "ean",
        "Brand": "brand",
        "Category": "category",
        "Description": "description",
        "Price (gross)": "price",
        "Currency": "currency",
        "Stock": "stock",
        "Image URL": "image_urls",
    }

    def extract(self) -> Iterator[dict[str, Any]]:
        if not self.CSV_PATH.exists():
            raise FileNotFoundError(f"CSV not found: {self.CSV_PATH}")

        self._logger.info("Reading CSV: %s", self.CSV_PATH)

        with self.CSV_PATH.open(encoding=self.ENCODING, newline="") as f:
            reader = csv.DictReader(f, delimiter=self.DELIMITER)
            for row in reader:
                yield self._remap(row)

    def _remap(self, row: dict[str, Any]) -> dict[str, Any]:
        """Apply COLUMN_MAP then add defaults for missing keys."""
        remapped = {
            self.COLUMN_MAP.get(k, k): v
            for k, v in row.items()
            if v is not None
        }
        # Handle multi-image column (pipe-separated URLs)
        if "image_urls" in remapped and isinstance(remapped["image_urls"], str):
            remapped["image_urls"] = [
                u.strip() for u in remapped["image_urls"].split("|") if u.strip()
            ]
        remapped.setdefault("metadata", {"source": self.SOURCE_NAME})
        return remapped
