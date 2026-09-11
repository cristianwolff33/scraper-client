from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class Product:
    """
    Canonical product model. Every adapter must produce this shape.
    Every exporter must consume only this shape.
    No business logic lives here — this is a pure value object.
    """

    sku: str
    name: str

    ean: str = ""
    brand: str = ""
    category: str = ""
    description: str = ""
    parameters: dict[str, str] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)
    price: Decimal | None = None
    currency: str = "PLN"
    stock: int | None = None
    image_urls: list[str] = field(default_factory=list)
    downloaded_images: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_source: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sku or not self.sku.strip():
            raise ValueError("Product.sku cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Product.name cannot be empty")
        self.sku = self.sku.strip()
        self.name = self.name.strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "ean": self.ean,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "description": self.description,
            "parameters": self.parameters,
            "attributes": self.attributes,
            "price": str(self.price) if self.price is not None else None,
            "currency": self.currency,
            "stock": self.stock,
            "image_urls": self.image_urls,
            "downloaded_images": self.downloaded_images,
            "metadata": self.metadata,
        }
