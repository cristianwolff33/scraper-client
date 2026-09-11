from __future__ import annotations

import time
from abc import abstractmethod
from enum import Enum
from typing import Any, Iterator

import requests

from core.browser import FetchMode, HttpClient
from core.cache import Cache
from core.config import Settings
from core.extractor import BaseExtractor
from core.logger import get_logger


_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class AdapterMode(Enum):
    REQUESTS = "requests"
    PLAYWRIGHT = "playwright"
    API = "api"
    XML_FEED = "xml_feed"
    CSV_FILE = "csv_file"


class BaseAdapter(BaseExtractor):
    """
    Base class for all data source adapters.

    Responsibility: extract raw data only.
    Rules:
      - No business logic
      - No normalization
      - No transformation
      - No export

    Subclasses override:
      - MODE: declared fetch strategy (no auto-detection needed at runtime)
      - extract(): yield raw dicts
      - setup() / teardown(): manage connections
    """

    MODE: AdapterMode = AdapterMode.REQUESTS
    SOURCE_NAME: str = "unnamed"

    def __init__(self, settings: Settings, cache: Cache) -> None:
        self._settings = settings
        self._cache = cache
        self._logger = get_logger(
            self.__class__.__name__,
            level=settings.log_level,
            log_dir=settings.logs_dir,
        )
        self._client: HttpClient | None = None

    def setup(self) -> None:
        if self.MODE in {AdapterMode.REQUESTS, AdapterMode.API, AdapterMode.XML_FEED}:
            self._client = HttpClient(
                user_agent=self._settings.browser.user_agent,
                timeout=self._settings.browser.timeout_ms // 1000,
                delay=self._settings.request_delay_seconds,
            )

    def teardown(self) -> None:
        if self._client:
            self._client.close()

    @abstractmethod
    def extract(self) -> Iterator[dict[str, Any]]:
        """Yield one raw record per product. Override in each adapter."""
        ...

    def get_page(self, url: str, **kwargs: Any) -> Any:
        """Convenience: fetch HTML via HttpClient with retry."""
        if not self._client:
            raise RuntimeError("Adapter not set up. Use as a context manager.")

        delay = self._settings.retry.initial_delay
        last_exc: Exception | None = None

        for attempt in range(1, self._settings.retry.max_attempts + 1):
            try:
                return self._client.get(url, **kwargs)
            except requests.HTTPError as exc:
                last_exc = exc
                status = exc.response.status_code if exc.response is not None else None
                if status not in _RETRYABLE_STATUS_CODES:
                    raise
            except (requests.ConnectionError, requests.Timeout, TimeoutError) as exc:
                last_exc = exc

            if attempt == self._settings.retry.max_attempts:
                break

            self._logger.warning(
                "GET failed for %s (attempt %d/%d): %s; retrying in %.1fs",
                url,
                attempt,
                self._settings.retry.max_attempts,
                last_exc,
                delay,
            )
            time.sleep(delay)
            delay = min(
                delay * self._settings.retry.backoff_multiplier,
                self._settings.retry.max_delay,
            )

        if last_exc:
            raise last_exc
        raise RuntimeError(f"GET failed for {url}")

    def is_visited(self, url: str) -> bool:
        return self._cache.is_visited(url)

    def mark_visited(self, url: str) -> None:
        self._cache.mark_visited(url)
