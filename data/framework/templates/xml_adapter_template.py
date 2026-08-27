"""
XML Feed Adapter Template
==========================
Copy to: adapters/<source_name>/adapter.py
Use for XML product feeds, sitemaps, and data exports.
"""
from __future__ import annotations

from typing import Any, Iterator
import xml.etree.ElementTree as ET

from adapters.base_adapter import AdapterMode, BaseAdapter
from core.cache import Cache
from core.config import Settings


class XmlFeedAdapter(BaseAdapter):
    """
    Adapter for an XML product feed.
    Handles remote XML files or local XML files.
    """

    MODE = AdapterMode.XML_FEED
    SOURCE_NAME = "xml_feed_example"

    FEED_URL = "https://example.com/feed.xml"  # TODO: set actual URL
    # TODO: set XPath-like element names for your feed structure
    PRODUCT_TAG = "product"       # XML tag wrapping each product
    NAMESPACE = ""                # set if feed uses XML namespaces, e.g. "{http://...}"

    def extract(self) -> Iterator[dict[str, Any]]:
        self._logger.info("Fetching XML feed: %s", self.FEED_URL)
        resp = self.get_page(self.FEED_URL)
        root = ET.fromstring(resp.text)

        tag = f"{self.NAMESPACE}{self.PRODUCT_TAG}"
        elements = root.findall(f".//{tag}")
        self._logger.info("Found %d product elements", len(elements))

        for el in elements:
            try:
                yield self._parse_element(el)
            except Exception as exc:
                self._logger.error("XML parse error: %s", exc)

    def _parse_element(self, el: ET.Element) -> dict[str, Any]:
        """
        TODO: Map XML element children to raw dict keys.
        """
        ns = self.NAMESPACE

        def text(tag: str) -> str:
            child = el.find(f"{ns}{tag}")
            return child.text.strip() if child is not None and child.text else ""

        def text_list(tag: str) -> list[str]:
            return [c.text.strip() for c in el.findall(f"{ns}{tag}") if c.text]

        return {
            "sku": text("sku") or text("id"),       # TODO: adjust tags
            "name": text("name") or text("title"),
            "ean": text("ean") or text("barcode"),
            "brand": text("brand") or text("manufacturer"),
            "category": text("category"),
            "description": text("description"),
            "price": text("price") or text("price_gross"),
            "currency": text("currency") or "PLN",
            "stock": text("stock") or text("quantity"),
            "image_urls": text_list("image"),
            "metadata": {"source": self.SOURCE_NAME},
        }
