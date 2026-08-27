"""
Transformer Template
======================
Copy to: adapters/<source_name>/transformer.py
Override only the fields that differ from ProductNormalizer defaults.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from models.product import Product
from transformers.product_normalizer import ProductNormalizer


class ExampleTransformer(ProductNormalizer):
    """
    Transformer for <SOURCE NAME>.
    Inherits all defaults from ProductNormalizer; override only source-specific logic.
    """

    DEFAULT_CURRENCY = "PLN"  # TODO: set if different

    def transform(self, raw: dict[str, Any]) -> Product:
        # Call parent to get defaults, then override specific fields
        product = super().transform(raw)

        # TODO: apply source-specific overrides
        # product.brand = self._extract_brand(raw)
        # product.category = self._build_category_path(raw)

        return product

    # --- Override specific extraction methods as needed ---

    def _sku(self, raw: dict[str, Any]) -> str:
        # TODO: override if SKU is in a non-standard location
        return super()._sku(raw)

    def _category(self, raw: dict[str, Any]) -> str:
        # TODO: build breadcrumb path if nested categories
        # breadcrumb = raw.get("category_path", [])
        # return " > ".join(breadcrumb) if breadcrumb else raw.get("category", "")
        return super()._category(raw)

    def _image_urls(self, raw: dict[str, Any]) -> list[str]:
        # TODO: handle source-specific image structure
        return super()._image_urls(raw)
