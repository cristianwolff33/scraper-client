"""
REST API Adapter Template
==========================
Copy to: adapters/<source_name>/adapter.py
Use for JSON REST APIs — no HTML parsing needed.
"""
from __future__ import annotations

from typing import Any, Iterator

from adapters.base_adapter import AdapterMode, BaseAdapter
from core.cache import Cache
from core.config import Settings


class ApiAdapter(BaseAdapter):
    """
    Adapter for <API NAME>.
    Handles pagination, authentication, and raw record extraction.
    """

    MODE = AdapterMode.API
    SOURCE_NAME = "api_example"

    # TODO: Replace with actual API base URL
    BASE_URL = "https://api.example.com/v1"

    def __init__(self, settings: Settings, cache: Cache) -> None:
        super().__init__(settings, cache)
        # TODO: Load API key from settings or environment
        # self._api_key = settings.extra.get("api_key", os.getenv("API_KEY", ""))

    def setup(self) -> None:
        super().setup()
        if self._client:
            # TODO: Set authentication headers
            # self._client._session.headers["Authorization"] = f"Bearer {self._api_key}"
            pass

    def extract(self) -> Iterator[dict[str, Any]]:
        page = 1
        per_page = 100  # TODO: adjust for this API

        while True:
            resp = self.get_page(
                f"{self.BASE_URL}/products",
                params={"page": page, "per_page": per_page},
            )
            data = resp.json()

            # TODO: adapt to actual API response shape
            items: list[dict[str, Any]] = data.get("data", data.get("items", []))
            if not items:
                break

            for item in items:
                yield self._normalize_raw(item)

            # TODO: adapt pagination detection to this API
            if len(items) < per_page:
                break
            page += 1

    def _normalize_raw(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Minimal field aliasing only — remap API field names to standard keys.
        Full normalization happens in the transformer.
        """
        return {
            # TODO: map API fields to standard names
            "sku": item.get("id", item.get("sku")),
            "name": item.get("name", item.get("title")),
            "ean": item.get("ean", item.get("barcode")),
            "brand": item.get("brand"),
            "category": item.get("category"),
            "description": item.get("description"),
            "price": item.get("price"),
            "currency": item.get("currency", "PLN"),
            "stock": item.get("stock", item.get("quantity")),
            "image_urls": item.get("images", []),
            "parameters": item.get("parameters", item.get("specs", {})),
            "attributes": item.get("attributes", {}),
            "metadata": {"source": self.SOURCE_NAME},
        }
