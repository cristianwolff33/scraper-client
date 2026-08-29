from __future__ import annotations

from typing import Any

from models.product import Product
from transformers.product_normalizer import ProductNormalizer


class PolskieFlagiTransformer(ProductNormalizer):
    """Transformer for polskieflagi.pl products."""

    DEFAULT_CURRENCY = "PLN"

    def transform(self, raw: dict[str, Any]) -> Product:
        return super().transform(raw)
