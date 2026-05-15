import asyncio
import random
import logging
from functools import wraps
from typing import Callable, Awaitable, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
):
    """
    Retry decorator with exponential backoff and optional jitter.

    :param max_attempts: Maximum number of attempts.
    :param base_delay: Base delay between retries in seconds.
    :param max_delay: Maximum delay between retries in seconds.
    :param jitter: Whether to add jitter to delay.
    :param exceptions: Tuple of exceptions that will trigger retries.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    logger.warning(
                        "Attempt %s/%s failed: %s",
                        attempt,
                        max_attempts,
                        exc,
                    )
                    if attempt == max_attempts:
                        break

                    delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    if jitter:
                        delay *= random.uniform(0.7, 1.3)

                    await asyncio.sleep(delay)

            raise last_exc or RuntimeError("Maximum retry attempts reached")

        return wrapper

    return decorator
