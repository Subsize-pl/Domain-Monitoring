import asyncio
import random
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class RetryResult(Generic[T]):
    value: T
    attempts: int


class RetryExhausted(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, *, attempts: int, last_exc: BaseException) -> None:
        super().__init__(
            f"Exhausted {attempts} attempt(s). "
            f"Last: {type(last_exc).__name__}: {last_exc}"
        )
        self.attempts = attempts
        self.last_exc = last_exc


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    max_attempts: int,
    base_delay: float,
    max_delay: float,
    retry_if: Callable[[BaseException], bool] | None = None,
    jitter: bool = True,
) -> RetryResult[T]:
    """
    Retry async callable with exponential backoff and optional jitter.

    :param func: Async callable to execute.
    :param max_attempts: Maximum number of attempts.
    :param base_delay: Initial retry delay in seconds.
    :param max_delay: Maximum retry delay in seconds.
    :param retry_if: Predicate to determine whether exception is retryable.
    :param jitter: Whether to apply random jitter to delay.

    :returns: RetryResult containing value and attempt metadata.

    :raises RetryExhausted: If all retry attempts fail.
    :raises Exception: If retry_if returns False for an exception.
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    last_exc: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            value = await func()
            return RetryResult(value=value, attempts=attempt)

        except Exception as exc:
            if retry_if is not None and not retry_if(exc):
                raise

            last_exc = exc

            if attempt == max_attempts:
                break

            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            if jitter:
                delay *= random.uniform(0.7, 1.3)
            await asyncio.sleep(delay)

    raise RetryExhausted(
        attempts=max_attempts,
        last_exc=last_exc
        or RuntimeError(
            "retry failed without captured exception",
        ),
    )
