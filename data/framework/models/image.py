from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ImageStatus(Enum):
    PENDING = "pending"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Image:
    """Tracks one image through the download pipeline."""

    url: str
    sku: str
    index: int = 0
    filename: str = ""
    local_path: Path | None = None
    status: ImageStatus = ImageStatus.PENDING
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.filename:
            suffix = f"_{self.index}" if self.index > 0 else ""
            self.filename = f"{self.sku}{suffix}.jpg"

    @property
    def is_downloaded(self) -> bool:
        return self.status == ImageStatus.DOWNLOADED

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "sku": self.sku,
            "index": self.index,
            "filename": self.filename,
            "local_path": str(self.local_path) if self.local_path else None,
            "status": self.status.value,
            "error": self.error,
        }
