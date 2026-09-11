from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from dataclasses import dataclass, field


@dataclass
class DownloadSettings:
    parallel_workers: int = 8
    timeout_seconds: int = 30
    max_retries: int = 3
    skip_existing: bool = True
    browser_fallback: bool = False
    browser_first: bool = False


@dataclass
class RetrySettings:
    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0


@dataclass
class BrowserSettings:
    headless: bool = True
    timeout_ms: int = 30_000
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    viewport_width: int = 1920
    viewport_height: int = 1080


@dataclass
class Settings:
    """Single source of truth for all runtime configuration."""

    project_name: str = "scraper-framework"
    output_dir: Path = Path("output")
    log_level: str = "INFO"
    default_currency: str = "PLN"
    request_delay_seconds: float = 0.5

    download: DownloadSettings = field(default_factory=DownloadSettings)
    retry: RetrySettings = field(default_factory=RetrySettings)
    browser: BrowserSettings = field(default_factory=BrowserSettings)

    extra: dict[str, Any] = field(default_factory=dict)
    images_subdir: str = ""

    @property
    def images_dir(self) -> Path:
        base = self.output_dir / "images"
        return base / self.images_subdir if self.images_subdir else base

    @property
    def logs_dir(self) -> Path:
        return self.output_dir / "logs"

    @property
    def cache_dir(self) -> Path:
        return self.output_dir / "cache"

    @property
    def excel_dir(self) -> Path:
        return self.output_dir / "excel"

    @property
    def csv_dir(self) -> Path:
        return self.output_dir / "csv"

    @property
    def json_dir(self) -> Path:
        return self.output_dir / "json"

    @property
    def xml_dir(self) -> Path:
        return self.output_dir / "xml"


def load_settings(path: str | Path = "config.yaml") -> Settings:
    """Load settings from YAML, falling back to defaults for missing keys."""
    config_path = Path(path)
    if not config_path.exists():
        return Settings()

    with config_path.open() as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    settings = Settings(
        project_name=raw.get("project_name", "scraper-framework"),
        output_dir=Path(raw.get("output_dir", "output")),
        log_level=raw.get("log_level", "INFO"),
        default_currency=raw.get("default_currency", "PLN"),
        request_delay_seconds=raw.get("request_delay_seconds", 0.5),
        images_subdir=raw.get("images_subdir", ""),
        extra=raw.get("extra", {}),
    )

    if dl := raw.get("download"):
        settings.download = DownloadSettings(**dl)
    if rt := raw.get("retry"):
        settings.retry = RetrySettings(**rt)
    if br := raw.get("browser"):
        settings.browser = BrowserSettings(**br)

    return settings
