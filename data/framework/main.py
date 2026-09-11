"""
Scraper Framework — CLI Entrypoint

Usage:
    uv run python main.py --adapter source_name --export json
    uv run python main.py --adapter source_name --export json,excel,csv --no-images
    uv run python main.py --adapter source_name --config config.yaml
"""
from __future__ import annotations

import argparse
import sys
import logging

from core.config import load_settings
from core.logger import get_logger
from core.cache import Cache
from core.filesystem import Filesystem
from core.pipeline import ETLPipeline, PipelineConfig
from exporters import ExcelExporter, CsvExporter, JsonExporter, XmlExporter
from validators.product_validator import ProductValidator


ADAPTER_REGISTRY: dict[str, str] = {
    # Public framework registry. Keep brand/source-specific adapters in
    # local_adapters.py, which is ignored by git.
}

TRANSFORMER_REGISTRY: dict[str, str] = {
    # Public framework registry. Keep brand/source-specific transformers in
    # local_adapters.py, which is ignored by git.
}

try:
    from local_adapters import ADAPTER_REGISTRY as LOCAL_ADAPTER_REGISTRY
    from local_adapters import TRANSFORMER_REGISTRY as LOCAL_TRANSFORMER_REGISTRY
except ImportError:
    pass
else:
    ADAPTER_REGISTRY.update(LOCAL_ADAPTER_REGISTRY)
    TRANSFORMER_REGISTRY.update(LOCAL_TRANSFORMER_REGISTRY)

EXPORTER_MAP = {
    "json": JsonExporter,
    "csv": CsvExporter,
    "excel": ExcelExporter,
    "xlsx": ExcelExporter,
    "xml": XmlExporter,
}


def _load_class(dotted_path: str) -> type:
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scraper Framework — ETL pipeline runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--adapter", required=True, help="Adapter name")
    parser.add_argument(
        "--export",
        default="json",
        help="Comma-separated export formats: json,csv,excel,xml (default: json)",
    )
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--no-images", action="store_true", help="Skip image download")
    parser.add_argument("--images-subdir", default="", help="Subdirectory under output/images/ (e.g. lamix)")
    parser.add_argument("--skip-invalid", action="store_true", default=True)
    args = parser.parse_args(argv)

    adapter_name = args.adapter.lower()
    settings = load_settings(args.config)
    if args.images_subdir:
        settings.images_subdir = args.images_subdir
    elif not settings.images_subdir:
        settings.images_subdir = adapter_name
    fs = Filesystem(settings)
    logger = get_logger("main", level=settings.log_level, log_dir=fs.log_dir())

    if adapter_name not in ADAPTER_REGISTRY:
        logger.error(
            "Unknown adapter '%s'. Available: %s",
            adapter_name,
            ", ".join(ADAPTER_REGISTRY),
        )
        return 1

    logger.info("Starting pipeline: adapter=%s", adapter_name)

    # --- Build dependencies ---
    cache = Cache(fs.cache_file(f"{adapter_name}.db"))

    AdapterClass = _load_class(ADAPTER_REGISTRY[adapter_name])
    TransformerClass = _load_class(TRANSFORMER_REGISTRY.get(adapter_name, "transformers.product_normalizer.ProductNormalizer"))

    adapter = AdapterClass(settings, cache)
    transformer = TransformerClass()
    validator = ProductValidator()

    fmt_names = [f.strip().lower() for f in args.export.split(",")]
    exporters = []
    for fmt in fmt_names:
        if fmt not in EXPORTER_MAP:
            logger.warning("Unknown export format '%s' — skipping", fmt)
            continue
        exporters.append(EXPORTER_MAP[fmt]())

    if not exporters:
        logger.error("No valid export formats specified")
        return 1

    pipeline_cfg = PipelineConfig(
        source_name=adapter_name,
        skip_invalid=args.skip_invalid,
        download_images=not args.no_images,
        export_formats=fmt_names,
    )

    pipeline = ETLPipeline(
        extractor=adapter,
        transformer=transformer,
        validator=validator,
        exporters=exporters,
        settings=settings,
        pipeline_config=pipeline_cfg,
    )

    result = pipeline.run()

    logger.info(
        "Done — extracted=%d transformed=%d valid=%d exported=%d images=%d duration=%.1fs",
        result.extracted,
        result.transformed,
        result.valid,
        result.exported,
        result.images_downloaded,
        result.duration_seconds,
    )

    if result.errors:
        logger.warning("%d errors occurred — check logs/errors.log", len(result.errors))

    return 0


if __name__ == "__main__":
    sys.exit(main())
