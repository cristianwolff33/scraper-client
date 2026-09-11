from __future__ import annotations

import logging
from contextlib import contextmanager
from enum import Enum
from typing import Any, Generator

import requests
from requests import Session

logger = logging.getLogger(__name__)


class FetchMode(Enum):
    REQUESTS = "requests"
    PLAYWRIGHT = "playwright"


class HttpClient:
    """
    Thin wrapper around requests.Session with configurable headers, delay, and retry.
    Use this for all non-JS sites.
    """

    def __init__(
        self,
        user_agent: str,
        timeout: int = 30,
        delay: float = 0.5,
    ) -> None:
        self._timeout = timeout
        self._delay = delay
        self._session = Session()
        self._session.headers.update({"User-Agent": user_agent})

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        import time

        time.sleep(self._delay)
        resp = self._session.get(url, timeout=self._timeout, **kwargs)
        resp.raise_for_status()
        return resp

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        import time

        time.sleep(self._delay)
        resp = self._session.post(url, timeout=self._timeout, **kwargs)
        resp.raise_for_status()
        return resp

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


@contextmanager
def playwright_browser(
    headless: bool = True,
    user_agent: str = "",
    viewport: tuple[int, int] = (1920, 1080),
    timeout_ms: int = 30_000,
) -> Generator[Any, None, None]:
    """
    Context manager yielding a Playwright Page ready to use.
    Import is deferred so projects that never need Playwright don't pay for it.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=user_agent or None,
            viewport={"width": viewport[0], "height": viewport[1]},
        )
        context.set_default_timeout(timeout_ms)
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


def detect_fetch_mode(url: str) -> FetchMode:
    """
    Heuristic: probe the URL with requests. If it fails or returns empty body,
    switch to Playwright. Adapters may override this by declaring their mode explicitly.
    """
    try:
        resp = requests.head(url, timeout=10, allow_redirects=True)
        ct = resp.headers.get("content-type", "")
        if resp.status_code == 200 and "text/html" in ct:
            return FetchMode.REQUESTS
        return FetchMode.PLAYWRIGHT
    except Exception:
        return FetchMode.PLAYWRIGHT
