from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from models.product import Product


class BaseExporter(ABC):
    """
    Contract for the Export stage.
    Exporters consume Product objects only — they must not normalize data.
    """

    @abstractmethod
    def export(self, products: list[Product], destination: Path) -> Path:
        """
        Write products to destination and return the final file path.
        The destination argument is typically a directory; implementations
        construct the filename themselves.
        """
        ...

    def supports_streaming(self) -> bool:
        """Override to True if the exporter can write incrementally."""
        return False
