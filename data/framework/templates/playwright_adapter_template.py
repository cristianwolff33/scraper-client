"""
Playwright Adapter Template
============================
Copy to: adapters/<source_name>/adapter.py
Use for JS-heavy sites, infinite scroll, Cloudflare-protected pages.
"""
from __future__ import annotations

from typing import Any, Iterator

from adapters.base_adapter import AdapterMode, BaseAdapter
from core.browser import playwright_browser
from core.cache import Cache
from core.config import Settings


class PlaywrightAdapter(BaseAdapter):
    """
    Adapter for <SOURCE NAME> using Playwright.
    Uses real browser — slower but handles JS rendering and bot protection.
    """

    MODE = AdapterMode.PLAYWRIGHT
    SOURCE_NAME = "playwright_example"

    BASE_URL = "https://example.com"  # TODO: set actual URL

    def __init__(self, settings: Settings, cache: Cache) -> None:
        super().__init__(settings, cache)
        # TODO: add any source-specific config

    def extract(self) -> Iterator[dict[str, Any]]:
        """
        Uses Playwright context manager for browser lifecycle.
        Each page interaction yields one raw product dict.
        """
        browser_cfg = self._settings.browser

        with playwright_browser(
            headless=browser_cfg.headless,
            user_agent=browser_cfg.user_agent,
            viewport=(browser_cfg.viewport_width, browser_cfg.viewport_height),
            timeout_ms=browser_cfg.timeout_ms,
        ) as page:
            # TODO: handle login if required
            # self._login(page)

            product_urls = self._collect_urls(page)
            self._logger.info("Found %d product URLs", len(product_urls))

            for url in product_urls:
                if self.is_visited(url):
                    continue
                try:
                    raw = self._extract_product(page, url)
                    if raw:
                        yield raw
                    self.mark_visited(url)
                except Exception as exc:
                    self._logger.error("Failed: %s — %s", url, exc)

    def _collect_urls(self, page: Any) -> list[str]:
        """
        TODO: Navigate listing pages and collect product URLs.
        Handle pagination or infinite scroll here.
        """
        urls: list[str] = []

        page.goto(self.BASE_URL)
        # TODO: implement pagination loop
        # while True:
        #     links = page.locator("a.product-link").all()
        #     urls += [link.get_attribute("href") for link in links]
        #     next_btn = page.locator("a.next-page")
        #     if not next_btn.count():
        #         break
        #     next_btn.click()
        #     page.wait_for_load_state("networkidle")

        return urls

    def _extract_product(self, page: Any, url: str) -> dict[str, Any] | None:
        """
        TODO: Navigate to product page and extract raw data.
        """
        page.goto(url)
        page.wait_for_load_state("domcontentloaded")

        # TODO: extract fields using page.locator() or page.evaluate()
        # TODO: parse the specification/parameters table if the source has one, e.g.:
        # parameters = {
        #     row.locator(".name").inner_text(): row.locator(".value").inner_text()
        #     for row in page.locator(".product-params tr").all()
        # }
        return {
            "sku": "",          # TODO
            "name": "",         # TODO
            "ean": "",
            "brand": "",
            "category": "",
            "description": "",
            "parameters": {},   # e.g. {"Color": "black", "Weight": "2kg"}
            "price": None,
            "currency": "PLN",
            "stock": None,
            "image_urls": [],
            "metadata": {"source_url": url},
        }

    def _login(self, page: Any) -> None:
        """
        TODO: implement if the site requires authentication.
        """
        pass
