from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    exceptions: tuple[type[Exception], ...] = (Exception,)


def with_retry(config: RetryConfig | None = None) -> Callable[[F], F]:
    """
    Decorator factory for exponential-backoff retry.

    Usage:
        @with_retry(RetryConfig(max_attempts=5, initial_delay=2.0))
        def fetch(url: str) -> str: ...
    """
    cfg = config or RetryConfig()

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = cfg.initial_delay
            last_exc: Exception | None = None

            for attempt in range(1, cfg.max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except cfg.exceptions as exc:
                    last_exc = exc
                    if attempt == cfg.max_attempts:
                        break
                    logger.warning(
                        "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                        fn.__name__,
                        attempt,
                        cfg.max_attempts,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    delay = min(delay * cfg.backoff_multiplier, cfg.max_delay)

            logger.error(
                "%s exhausted %d attempts. Last error: %s",
                fn.__name__,
                cfg.max_attempts,
                last_exc,
            )
            raise last_exc  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator
