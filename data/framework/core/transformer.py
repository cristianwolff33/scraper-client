from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from models.product import Product


class BaseTransformer(ABC):
    """
    Contract for the Transform + Normalize stage.
    Receives a raw dict from an extractor; returns a Product.
    All field mapping and normalization lives here, never in adapters or exporters.
    """

    @abstractmethod
    def transform(self, raw: dict[str, Any]) -> Product:
        """Map raw extracted data to the canonical Product model."""
        ...

    def transform_many(self, raws: list[dict[str, Any]]) -> list[Product]:
        products = []
        for raw in raws:
            try:
                products.append(self.transform(raw))
            except Exception as exc:
                self._on_error(raw, exc)
        return products

    def _on_error(self, raw: dict[str, Any], exc: Exception) -> None:
        import logging
        logging.getLogger(self.__class__.__name__).error(
            "Transform failed for raw=%r: %s", raw, exc
        )
