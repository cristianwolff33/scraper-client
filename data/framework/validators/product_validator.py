from __future__ import annotations

import re
from decimal import Decimal

from core.validator import BaseValidator, Severity, ValidationIssue, ValidationResult
from models.product import Product


class ProductValidator(BaseValidator):
    """
    Default validator covering the most common data quality issues.
    Extend or replace individual check methods to customize per-project.
    """

    MIN_PRICE: Decimal = Decimal("0.01")
    MAX_PRICE: Decimal = Decimal("1_000_000")

    def __init__(self, seen_skus: set[str] | None = None) -> None:
        self._seen_skus: set[str] = seen_skus if seen_skus is not None else set()

    def validate(self, product: Product) -> ValidationResult:
        issues: list[ValidationIssue] = []

        issues += self._check_sku(product)
        issues += self._check_name(product)
        issues += self._check_category(product)
        issues += self._check_price(product)
        issues += self._check_images(product)

        return ValidationResult(product=product, issues=issues)

    def _check_sku(self, product: Product) -> list[ValidationIssue]:
        issues = []
        if not product.sku:
            issues.append(ValidationIssue("sku", "SKU is empty", Severity.ERROR))
        elif product.sku in self._seen_skus:
            issues.append(
                ValidationIssue("sku", f"Duplicate SKU: {product.sku}", Severity.ERROR)
            )
        else:
            self._seen_skus.add(product.sku)
        return issues

    def _check_name(self, product: Product) -> list[ValidationIssue]:
        if not product.name:
            return [ValidationIssue("name", "Product name is empty", Severity.ERROR)]
        return []

    def _check_category(self, product: Product) -> list[ValidationIssue]:
        if not product.category:
            return [
                ValidationIssue("category", "Category is missing", Severity.WARNING)
            ]
        return []

    def _check_price(self, product: Product) -> list[ValidationIssue]:
        if product.price is None:
            return [ValidationIssue("price", "Price is missing", Severity.WARNING)]
        if product.price < self.MIN_PRICE:
            return [
                ValidationIssue(
                    "price",
                    f"Price {product.price} is below minimum {self.MIN_PRICE}",
                    Severity.ERROR,
                )
            ]
        if product.price > self.MAX_PRICE:
            return [
                ValidationIssue(
                    "price",
                    f"Price {product.price} exceeds maximum {self.MAX_PRICE}",
                    Severity.WARNING,
                )
            ]
        return []

    def _check_images(self, product: Product) -> list[ValidationIssue]:
        issues = []
        for url in product.image_urls:
            if not re.match(r"^https?://", url):
                issues.append(
                    ValidationIssue(
                        "image_urls",
                        f"Invalid image URL: {url}",
                        Severity.WARNING,
                    )
                )
        return issues
