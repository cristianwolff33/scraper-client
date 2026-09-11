from __future__ import annotations

from typing import Any

from core.transformer import BaseTransformer
from core.utils import clean_text, parse_price
from models.product import Product


class ProductNormalizer(BaseTransformer):
    """
    Default transformer for generic product data.
    Adapter-specific transformers should subclass this and override only
    the fields that differ — avoiding duplication of common normalization logic.
    """

    DEFAULT_CURRENCY: str = "PLN"

    def transform(self, raw: dict[str, Any]) -> Product:
        return Product(
            sku=self._sku(raw),
            name=self._name(raw),
            ean=raw.get("ean", raw.get("barcode", "")),
            brand=raw.get("brand", raw.get("manufacturer", "")),
            category=self._category(raw),
            description=clean_text(raw.get("description", raw.get("desc", ""))),
            parameters=self._parameters(raw),
            attributes=raw.get("attributes", {}),
            price=parse_price(raw.get("price", raw.get("price_gross"))),
            currency=raw.get("currency", self.DEFAULT_CURRENCY),
            stock=self._stock(raw),
            image_urls=self._image_urls(raw),
            metadata=raw.get("metadata", {}),
            raw_source=raw,
        )

    def _sku(self, raw: dict[str, Any]) -> str:
        for key in ("sku", "id", "product_id", "code", "symbol"):
            if v := raw.get(key):
                return str(v).strip()
        raise ValueError(f"Cannot determine SKU from keys: {list(raw.keys())}")

    def _name(self, raw: dict[str, Any]) -> str:
        for key in ("name", "title", "product_name", "label"):
            if v := raw.get(key):
                return clean_text(str(v))
        raise ValueError("Cannot determine product name")

    def _category(self, raw: dict[str, Any]) -> str:
        for key in ("category", "category_name", "cat", "category_path"):
            if v := raw.get(key):
                return str(v).strip()
        return ""

    def _parameters(self, raw: dict[str, Any]) -> dict[str, str]:
        params = raw.get("parameters", raw.get("specs", raw.get("features", {})))
        if isinstance(params, dict):
            return {str(k): str(v) for k, v in params.items()}
        return {}

    def _stock(self, raw: dict[str, Any]) -> int | None:
        for key in ("stock", "quantity", "qty", "availability"):
            if (v := raw.get(key)) is not None:
                try:
                    return int(v)
                except (ValueError, TypeError):
                    return None
        return None

    def _image_urls(self, raw: dict[str, Any]) -> list[str]:
        for key in ("image_urls", "images", "photos", "image_url", "photo"):
            v = raw.get(key)
            if isinstance(v, list):
                return [str(u) for u in v if u]
            if isinstance(v, str) and v:
                return [v]
        return []
