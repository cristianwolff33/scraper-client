from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from core.cache import Cache
from core.config import Settings
from core.downloader import ImageDownloader
from core.exporter import BaseExporter
from core.extractor import BaseExtractor
from core.filesystem import Filesystem
from core.transformer import BaseTransformer
from core.validator import BaseValidator, ValidationResult
from models.product import Product

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    extracted: int = 0
    transformed: int = 0
    valid: int = 0
    invalid: int = 0
    exported: int = 0
    images_downloaded: int = 0
    errors: list[str] = field(default_factory=list)
    validation_issues: list[ValidationResult] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        if not self.transformed:
            return 0.0
        return self.valid / self.transformed


@dataclass
class PipelineConfig:
    """
    Declarative configuration for one pipeline run.
    Separate from Settings so a single settings file can serve many pipelines.
    """

    source_name: str
    skip_invalid: bool = True
    download_images: bool = True
    export_formats: list[str] = field(default_factory=lambda: ["json"])
    batch_size: int = 100


class ETLPipeline:
    """
    Orchestrates the full ETL flow:
        Extract → Transform → Validate → Export → Download Images

    No stage may be bypassed. All dependencies are injected — the pipeline
    itself has zero knowledge of concrete adapters, websites, or formats.
    """

    def __init__(
        self,
        extractor: BaseExtractor,
        transformer: BaseTransformer,
        validator: BaseValidator,
        exporters: list[BaseExporter],
        settings: Settings,
        pipeline_config: PipelineConfig | None = None,
    ) -> None:
        self._extractor = extractor
        self._transformer = transformer
        self._validator = validator
        self._exporters = exporters
        self._cfg = pipeline_config or PipelineConfig(source_name="unknown")
        self._settings = (
            replace(settings, images_subdir=self._cfg.source_name)
            if not settings.images_subdir
            else settings
        )

        self._fs = Filesystem(self._settings)
        self._cache = Cache(self._fs.cache_file(f"{self._cfg.source_name}.db"))
        self._downloader = ImageDownloader(
            filesystem=self._fs,
            cache=self._cache,
            workers=self._settings.download.parallel_workers,
            timeout=self._settings.download.timeout_seconds,
            max_retries=self._settings.download.max_retries,
            browser_fallback=(
                self._settings.download.browser_fallback
                or bool(getattr(extractor, "USE_PLAYWRIGHT_IMAGE_FALLBACK", False))
                or bool(getattr(extractor, "USE_PLAYWRIGHT_IMAGE_DOWNLOADER", False))
            ),
            browser_first=(
                self._settings.download.browser_first
                or bool(getattr(extractor, "USE_PLAYWRIGHT_IMAGE_DOWNLOADER", False))
            ),
            browser_user_agent=self._settings.browser.user_agent,
            browser_viewport=(
                self._settings.browser.viewport_width,
                self._settings.browser.viewport_height,
            ),
            browser_timeout_ms=self._settings.browser.timeout_ms,
        )

    def run(self) -> PipelineResult:
        result = PipelineResult()
        started = time.monotonic()

        logger.info("Pipeline started: source=%s", self._cfg.source_name)

        products: list[Product] = []

        # --- Extract → Transform ---
        with self._extractor:
            for raw in self._extractor.extract():
                result.extracted += 1
                try:
                    product = self._transformer.transform(raw)
                    result.transformed += 1
                    products.append(product)
                except Exception as exc:
                    msg = f"Transform error on record #{result.extracted}: {exc}"
                    result.errors.append(msg)
                    logger.error(msg)

        logger.info(
            "Extract+Transform complete: %d extracted, %d transformed",
            result.extracted,
            result.transformed,
        )

        # --- Validate ---
        valid_products: list[Product] = []
        for vr in self._validator.validate_many(products):
            result.validation_issues.append(vr)
            if vr.is_valid:
                result.valid += 1
                valid_products.append(vr.product)
            else:
                result.invalid += 1
                for issue in vr.errors:
                    logger.warning(
                        "Validation error [%s.%s]: %s",
                        vr.product.sku,
                        issue.field,
                        issue.message,
                    )
                if not self._cfg.skip_invalid:
                    valid_products.append(vr.product)

        logger.info(
            "Validation complete: %d valid, %d invalid",
            result.valid,
            result.invalid,
        )

        export_targets = valid_products if self._cfg.skip_invalid else products

        # --- Export ---
        for exporter in self._exporters:
            fmt = exporter.__class__.__name__.lower().replace("exporter", "")
            try:
                dest = self._fs.export_path(fmt, self._cfg.source_name)
                out_path = exporter.export(export_targets, dest)
                result.exported += len(export_targets)
                logger.info("Exported %d products to %s", len(export_targets), out_path)
            except Exception as exc:
                msg = f"Export error ({fmt}): {exc}"
                result.errors.append(msg)
                logger.error(msg)

        # --- Download Images ---
        if self._cfg.download_images:
            self._downloader.download_for_products(export_targets)
            result.images_downloaded = sum(
                len(p.downloaded_images) for p in export_targets
            )
            logger.info("Images downloaded: %d", result.images_downloaded)

        result.duration_seconds = time.monotonic() - started
        logger.info(
            "Pipeline complete in %.1fs — %d valid products, %d images",
            result.duration_seconds,
            result.valid,
            result.images_downloaded,
        )
        self._cache.close()
        return result
