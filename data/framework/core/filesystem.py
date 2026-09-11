from __future__ import annotations

import re
from pathlib import Path

from .config import Settings


class Filesystem:
    """
    Central authority for all path resolution.
    No module should construct output paths independently.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for d in [
            self._settings.images_dir,
            self._settings.logs_dir,
            self._settings.cache_dir,
            self._settings.excel_dir,
            self._settings.csv_dir,
            self._settings.json_dir,
            self._settings.xml_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def image_path(self, sku: str, index: int = 0, ext: str = "jpg") -> Path:
        safe = self._safe_name(sku)
        suffix = f"_{index}" if index > 0 else ""
        return self._settings.images_dir / f"{safe}{suffix}.{ext}"

    def export_path(self, fmt: str, name: str) -> Path:
        dirs = {
            "excel": self._settings.excel_dir,
            "csv": self._settings.csv_dir,
            "json": self._settings.json_dir,
            "xml": self._settings.xml_dir,
        }
        directory = dirs.get(fmt, self._settings.output_dir)
        return directory / name

    def cache_file(self, name: str) -> Path:
        return self._settings.cache_dir / name

    def log_dir(self) -> Path:
        return self._settings.logs_dir

    @staticmethod
    def _safe_name(name: str) -> str:
        return re.sub(r"[^\w\-]", "_", name).strip("_") or "unnamed"
