from __future__ import annotations

import re
from pathlib import Path

from models.image import Image, ImageStatus


class ImageValidator:
    """Validates downloaded images before they are recorded as complete."""

    MIN_FILE_SIZE_BYTES: int = 1024
    ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})

    def validate(self, image: Image) -> bool:
        if not image.local_path or not image.local_path.exists():
            image.status = ImageStatus.FAILED
            image.error = "File does not exist"
            return False

        if image.local_path.stat().st_size < self.MIN_FILE_SIZE_BYTES:
            image.status = ImageStatus.FAILED
            image.error = f"File too small ({image.local_path.stat().st_size} bytes)"
            return False

        if image.local_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            image.status = ImageStatus.FAILED
            image.error = f"Unsupported extension: {image.local_path.suffix}"
            return False

        return True

    def validate_url(self, url: str) -> bool:
        return bool(re.match(r"^https?://", url))
