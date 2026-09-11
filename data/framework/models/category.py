from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Category:
    """Normalized category value object."""

    id: str
    name: str
    slug: str = ""
    parent_id: str | None = None
    breadcrumb: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_source: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Category.id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Category.name cannot be empty")

    @property
    def full_path(self) -> str:
        return " > ".join(self.breadcrumb) if self.breadcrumb else self.name

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "parent_id": self.parent_id,
            "breadcrumb": self.breadcrumb,
            "full_path": self.full_path,
            "metadata": self.metadata,
        }
