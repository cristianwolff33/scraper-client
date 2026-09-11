from __future__ import annotations

from typing import Any

from core.utils import slugify
from models.category import Category


class CategoryNormalizer:
    """
    Converts raw category dicts to Category value objects.
    Not a BaseTransformer because categories are a side-product of extraction,
    not the primary pipeline unit.
    """

    def normalize(self, raw: dict[str, Any]) -> Category:
        cat_id = str(raw.get("id", raw.get("category_id", ""))).strip()
        name = str(raw.get("name", raw.get("category_name", ""))).strip()

        if not cat_id:
            raise ValueError("Category raw data missing 'id'")
        if not name:
            raise ValueError("Category raw data missing 'name'")

        breadcrumb = raw.get("breadcrumb", raw.get("path", []))
        if isinstance(breadcrumb, str):
            breadcrumb = [b.strip() for b in breadcrumb.split(">") if b.strip()]

        return Category(
            id=cat_id,
            name=name,
            slug=raw.get("slug", slugify(name)),
            parent_id=str(raw["parent_id"]) if raw.get("parent_id") else None,
            breadcrumb=breadcrumb,
            metadata=raw.get("metadata", {}),
            raw_source=raw,
        )

    def normalize_many(self, raws: list[dict[str, Any]]) -> list[Category]:
        result = []
        for raw in raws:
            try:
                result.append(self.normalize(raw))
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning("Category normalize failed: %s", exc)
        return result
