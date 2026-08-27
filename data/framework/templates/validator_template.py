"""
Validator Template
====================
Copy to: adapters/<source_name>/validator.py (only if custom rules needed).
Extend ProductValidator — do NOT rewrite existing checks.
"""
from __future__ import annotations

from decimal import Decimal

from core.validator import Severity, ValidationIssue, ValidationResult
from models.product import Product
from validators.product_validator import ProductValidator


class ExampleValidator(ProductValidator):
    """
    Custom validator for <SOURCE NAME>.
    Add source-specific rules; all standard rules are inherited.
    """

    # TODO: override limits if source has different price ranges
    MIN_PRICE = Decimal("0.01")
    MAX_PRICE = Decimal("500_000")

    def validate(self, product: Product) -> ValidationResult:
        result = super().validate(product)

        # TODO: add source-specific validation rules
        result.issues += self._check_ean(product)
        result.issues += self._check_brand(product)

        return result

    def _check_ean(self, product: Product) -> list[ValidationIssue]:
        """Warn if EAN is missing — required by some marketplaces."""
        if not product.ean:
            return [ValidationIssue("ean", "EAN/barcode is missing", Severity.WARNING)]
        return []

    def _check_brand(self, product: Product) -> list[ValidationIssue]:
        """Error if brand is empty — required for this source."""
        if not product.brand:
            return [ValidationIssue("brand", "Brand is required", Severity.ERROR)]
        return []
