"""
Test Template
===============
Copy to: tests/test_<source_name>.py
Replace ExampleAdapter/Transformer/Validator with your concrete classes.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from core.config import load_settings
from models.product import Product
from validators.product_validator import ProductValidator


# --- Fixtures ---

@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def sample_raw():
    """Minimal raw dict that a transformer should handle."""
    return {
        "sku": "TEST-001",
        "name": "Test Product",
        "brand": "TestBrand",
        "category": "Test Category",
        "price": "19.99",
        "currency": "PLN",
        "stock": 10,
        "image_urls": ["https://example.com/img.jpg"],
    }


@pytest.fixture
def sample_product():
    return Product(
        sku="TEST-001",
        name="Test Product",
        brand="TestBrand",
        category="Test Category",
        price=Decimal("19.99"),
        currency="PLN",
        stock=10,
        image_urls=["https://example.com/img.jpg"],
    )


# --- Transformer Tests ---

class TestExampleTransformer:
    def test_transform_happy_path(self, sample_raw):
        from transformers.product_normalizer import ProductNormalizer  # TODO: swap for your transformer
        transformer = ProductNormalizer()
        product = transformer.transform(sample_raw)
        assert product.sku == "TEST-001"
        assert product.name == "Test Product"
        assert product.price == Decimal("19.99")

    def test_transform_missing_sku_raises(self):
        from transformers.product_normalizer import ProductNormalizer
        transformer = ProductNormalizer()
        with pytest.raises(ValueError):
            transformer.transform({"name": "No SKU"})

    def test_transform_price_string(self, sample_raw):
        from transformers.product_normalizer import ProductNormalizer
        transformer = ProductNormalizer()
        sample_raw["price"] = "1 234,99 zł"
        product = transformer.transform(sample_raw)
        assert product.price == Decimal("1234.99")


# --- Validator Tests ---

class TestProductValidator:
    def test_valid_product_passes(self, sample_product):
        validator = ProductValidator()
        result = validator.validate(sample_product)
        assert result.is_valid

    def test_missing_sku_fails(self):
        validator = ProductValidator()
        # Product.__post_init__ raises ValueError for empty SKU,
        # so we test transformer-level guard instead
        with pytest.raises(ValueError):
            Product(sku="", name="Test")

    def test_duplicate_sku_fails(self, sample_product):
        validator = ProductValidator(seen_skus={"TEST-001"})
        result = validator.validate(sample_product)
        assert not result.is_valid
        assert any("Duplicate" in i.message for i in result.errors)

    def test_missing_category_is_warning(self, sample_product):
        sample_product.category = ""
        validator = ProductValidator()
        result = validator.validate(sample_product)
        assert result.is_valid  # warning, not error
        assert any(i.field == "category" for i in result.warnings)

    def test_invalid_image_url_is_warning(self, sample_product):
        sample_product.image_urls = ["not-a-url"]
        validator = ProductValidator()
        result = validator.validate(sample_product)
        assert result.is_valid  # warning only
        assert any(i.field == "image_urls" for i in result.warnings)


# --- Adapter Tests (with mock HTTP) ---

class TestExampleAdapter:
    """
    TODO: Replace with your adapter class.
    Use patch to mock HTTP calls — never make real network requests in tests.
    """

    def test_adapter_skips_visited_url(self, settings):
        # TODO: import your adapter
        # from adapters.example.adapter import ExampleAdapter
        # cache = MagicMock()
        # cache.is_visited.return_value = True
        # adapter = ExampleAdapter(settings, cache)
        # ... assert no extract calls made
        pass

    def test_adapter_yields_raw_dicts(self, settings):
        # TODO: mock get_page and assert raw dicts are yielded
        pass
