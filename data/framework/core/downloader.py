from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import requests

from core.cache import Cache
from core.browser import playwright_browser
from core.filesystem import Filesystem
from core.retry import RetryConfig, with_retry
from models.image import Image, ImageStatus
from models.product import Product

logger = logging.getLogger(__name__)


class ImageDownloader:
    """
    Parallel image downloader with deduplication, resume, and retry support.
    Downloads happen after validation — never before.
    """

    def __init__(
        self,
        filesystem: Filesystem,
        cache: Cache,
        workers: int = 8,
        timeout: int = 30,
        max_retries: int = 3,
        on_progress: Callable[[Image], None] | None = None,
        browser_fallback: bool = False,
        browser_first: bool = False,
        browser_user_agent: str = "",
        browser_viewport: tuple[int, int] = (1920, 1080),
        browser_timeout_ms: int = 30_000,
    ) -> None:
        self._fs = filesystem
        self._cache = cache
        self._workers = workers
        self._timeout = timeout
        self._max_retries = max_retries
        self._on_progress = on_progress
        self._browser_fallback = browser_fallback
        self._browser_first = browser_first
        self._browser_user_agent = browser_user_agent
        self._request_headers = {
            "User-Agent": browser_user_agent
            or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        }
        self._browser_viewport = browser_viewport
        self._browser_timeout_ms = browser_timeout_ms
        self._retry_cfg = RetryConfig(
            max_attempts=max_retries,
            initial_delay=1.0,
            backoff_multiplier=2.0,
            exceptions=(requests.RequestException, OSError),
        )

    def download_for_products(self, products: list[Product]) -> list[Product]:
        """Download all images for a list of products, updating downloaded_images in-place."""
        images: list[Image] = []
        for product in products:
            for idx, url in enumerate(product.image_urls):
                path = self._fs.image_path(product.sku, index=idx)
                images.append(Image(url=url, sku=product.sku, index=idx, local_path=path))

        results = self._download_batch(images)

        sku_paths: dict[str, list[str]] = {}
        for img in results:
            if img.is_downloaded and img.local_path:
                sku_paths.setdefault(img.sku, []).append(str(img.local_path))

        for product in products:
            product.downloaded_images = sku_paths.get(product.sku, [])

        return products

    def _download_batch(self, images: list[Image]) -> list[Image]:
        if self._browser_first:
            self._download_browser_batch(images)
            return images

        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            futures = {pool.submit(self._download_one, img): img for img in images}
            for future in as_completed(futures):
                img = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    img.status = ImageStatus.FAILED
                    img.error = str(exc)
                    logger.error("Image download failed: %s — %s", img.url, exc)
                if self._on_progress:
                    self._on_progress(img)

        if self._browser_fallback:
            failed_images = [img for img in images if img.status == ImageStatus.FAILED]
            if failed_images:
                logger.info(
                    "Retrying %d failed image downloads with Playwright",
                    len(failed_images),
                )
                self._download_browser_batch(failed_images)

        return images

    def _download_one(self, image: Image) -> None:
        assert image.local_path is not None

        if self._cache.is_image_downloaded(image.url) and image.local_path.exists():
            image.status = ImageStatus.DOWNLOADED
            logger.debug("Using cached image: %s", image.url)
            return

        self._fetch_with_retry(image)

    @with_retry()
    def _fetch_with_retry(self, image: Image) -> None:
        assert image.local_path is not None
        resp = requests.get(
            image.url,
            timeout=self._timeout,
            stream=True,
            headers=self._request_headers,
        )
        resp.raise_for_status()

        image.local_path.parent.mkdir(parents=True, exist_ok=True)
        with image.local_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        image.status = ImageStatus.DOWNLOADED
        self._cache.mark_image_downloaded(image.url, str(image.local_path))
        logger.debug("Downloaded: %s → %s", image.url, image.local_path)

    def _download_browser_batch(self, images: list[Image]) -> None:
        try:
            with playwright_browser(
                headless=True,
                user_agent=self._browser_user_agent,
                viewport=self._browser_viewport,
                timeout_ms=self._browser_timeout_ms,
            ) as page:
                for image in images:
                    try:
                        self._fetch_with_browser(page, image)
                    except Exception as exc:
                        image.status = ImageStatus.FAILED
                        image.error = str(exc)
                        logger.error(
                            "Browser image download failed: %s — %s",
                            image.url,
                            exc,
                        )
                    if self._on_progress:
                        self._on_progress(image)
        except Exception as exc:
            for image in images:
                image.status = ImageStatus.FAILED
                image.error = str(exc)
            logger.error("Could not start browser image fallback: %s", exc)

    def _fetch_with_browser(self, page: object, image: Image) -> None:
        assert image.local_path is not None

        if self._cache.is_image_downloaded(image.url) and image.local_path.exists():
            image.status = ImageStatus.DOWNLOADED
            image.error = ""
            logger.debug("Using cached image: %s", image.url)
            return

        response = page.goto(
            image.url,
            wait_until="domcontentloaded",
            timeout=self._browser_timeout_ms,
        )
        if response is None:
            raise RuntimeError("Browser did not return a response")
        if response.status >= 400:
            raise RuntimeError(f"Browser returned HTTP {response.status}")

        body = response.body()
        content_type = response.headers.get("content-type", "").lower()
        if not body:
            raise RuntimeError("Browser returned an empty image response")
        if "image/" not in content_type and not self._looks_like_image(body):
            raise RuntimeError(f"Browser returned non-image content: {content_type}")

        image.local_path.parent.mkdir(parents=True, exist_ok=True)
        with image.local_path.open("wb") as f:
            f.write(body)

        image.status = ImageStatus.DOWNLOADED
        image.error = ""
        self._cache.mark_image_downloaded(image.url, str(image.local_path))
        logger.debug("Downloaded with browser: %s → %s", image.url, image.local_path)

    def _looks_like_image(self, body: bytes) -> bool:
        return (
            body.startswith(b"\xff\xd8\xff")
            or body.startswith(b"\x89PNG\r\n\x1a\n")
            or body.startswith(b"GIF87a")
            or body.startswith(b"GIF89a")
            or body.startswith(b"RIFF")
        )
