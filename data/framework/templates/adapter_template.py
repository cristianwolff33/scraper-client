"""
HTML/Requests Adapter Template
================================
Copy this file to: adapters/<source_name>/adapter.py
Replace every TODO with source-specific logic.
Keep this file minimal — no business logic, no normalization.
"""
from __future__ import annotations

from typing import Any, Iterator

from adapters.base_adapter import AdapterMode, BaseAdapter
from core.cache import Cache
from core.config import Settings


class ExampleAdapter(BaseAdapter):
    """
    Adapter for <SOURCE NAME>.
    Responsibility: extract raw product data only.
    """

    MODE = AdapterMode.REQUESTS
    SOURCE_NAME = "example"

    # TODO: Set the base URL for this source
    BASE_URL = "https://example.com"

    def __init__(self, settings: Settings, cache: Cache) -> None:
        super().__init__(settings, cache)
        # TODO: Add any source-specific state (e.g., category IDs, filters)

    def setup(self) -> None:
        super().setup()
        # TODO: Authenticate if needed (set cookies, tokens, etc.)
        self._logger.info("Adapter ready: %s", self.SOURCE_NAME)

    def teardown(self) -> None:
        super().teardown()
        self._logger.info("Adapter teardown: %s", self.SOURCE_NAME)

    def extract(self) -> Iterator[dict[str, Any]]:
        """
        Main extraction loop.
        Yield one raw dict per product.
        Do NOT normalize — that is the transformer's job.
        """
        # TODO: Replace with actual URL discovery / pagination
        product_urls = self._get_product_urls()
        self._logger.info("Found %d product URLs", len(product_urls))

        for url in product_urls:
            if self.is_visited(url):
                self._logger.debug("Skipping visited: %s", url)
                continue

            try:
                raw = self._extract_product(url)
                if raw:
                    yield raw
                self.mark_visited(url)
            except Exception as exc:
                self._logger.error("Failed to extract %s: %s", url, exc)

    def _get_product_urls(self) -> list[str]:
        """
        TODO: Return all product page URLs.
        Implement pagination here.
        """
        # Example: paginate through a listing page
        urls = []
        page = 1
        while True:
            resp = self.get_page(f"{self.BASE_URL}/products?page={page}")
            # TODO: parse product links from resp.text using BS4/lxml
            # links = parse_links(resp.text)
            links: list[str] = []  # replace this

            if not links:
                break
            urls.extend(links)
            page += 1
        return urls

    def _extract_product(self, url: str) -> dict[str, Any] | None:
        """
        TODO: Fetch and parse one product page.
        Return raw dict with all available fields.
        Field names do not need to match Product model — transformer handles that.
        """
        resp = self.get_page(url)

        # TODO: parse with BeautifulSoup or lxml
        # from bs4 import BeautifulSoup
        # soup = BeautifulSoup(resp.text, "lxml")

        return {
            # TODO: fill in actual field extraction
            "sku": "",          # required
            "name": "",         # required
            "ean": "",
            "brand": "",
            "category": "",
            "description": "",
            "price": None,
            "currency": "PLN",
            "stock": None,
            "image_urls": [],
            "metadata": {"source_url": url},
        }
