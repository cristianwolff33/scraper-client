from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterator


class BaseExtractor(ABC):
    """
    Contract for the Extract stage.
    Implementations yield raw dicts — no business logic, no normalization.
    """

    @abstractmethod
    def extract(self) -> Iterator[dict[str, Any]]:
        """Yield one raw record per iteration."""
        ...

    def setup(self) -> None:
        """Called once before extraction begins. Override to open connections."""

    def teardown(self) -> None:
        """Called once after extraction ends. Override to close connections."""

    def __enter__(self) -> "BaseExtractor":
        self.setup()
        return self

    def __exit__(self, *_: Any) -> None:
        self.teardown()
