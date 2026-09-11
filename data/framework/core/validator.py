from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from models.product import Product


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    field: str
    message: str
    severity: Severity = Severity.ERROR


@dataclass
class ValidationResult:
    product: Product
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]


class BaseValidator(ABC):
    """
    Contract for the Validate stage.
    Returns ValidationResult so the pipeline can decide to skip, warn, or halt.
    """

    @abstractmethod
    def validate(self, product: Product) -> ValidationResult:
        ...

    def validate_many(self, products: list[Product]) -> list[ValidationResult]:
        return [self.validate(p) for p in products]
