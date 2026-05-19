import ssl
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone

import httpx

from domain_monitoring.core.utils.log.logger import get_logger
from domain_monitoring.core.utils.retry_async import (
    RetryExhausted,
    retry_async,
)
from domain_monitoring.monitoring.config import MonitoringConfig
from domain_monitoring.monitoring.models.domain_protocol import DomainProtocol
from domain_monitoring.monitoring.models.monitor_status import MonitorStatus
from domain_monitoring.monitoring.models.tls_status import TlsStatus

logger = get_logger(__name__)


@dataclass(slots=True)
class DomainCheckResult:
    domain_name: str
    checked_at: datetime
    status: MonitorStatus
    scheme_used: DomainProtocol | None
    tls_status: TlsStatus
    http_status_code: int | None
    latency_ms: int | None
    error_text: str | None
    attempt_count: int


def _is_tls_error(exc: BaseException) -> bool:
    if isinstance(exc, ssl.SSLError):
        return True
    if isinstance(exc, httpx.TransportError):
        cause = exc.__cause__ or exc.__context__
        if isinstance(cause, ssl.SSLError):
            return True
        msg = str(exc).lower()
        return any(kw in msg for kw in ("certificate", "ssl", "tls"))
    return False


def _is_retryable(exc: BaseException) -> bool:
    # Retry on transport errors EXCEPT TLS failures
    return isinstance(exc, httpx.TransportError) and not _is_tls_error(exc)


def _classify_http_status(code: int) -> tuple[MonitorStatus, str | None]:
    if code < 400:
        return MonitorStatus.up, None
    if code < 500:
        return MonitorStatus.up, f"HTTP {code}"
    return MonitorStatus.degraded, f"HTTP {code}"


async def _single_probe(
    client: httpx.AsyncClient,
    *,
    domain_name: str,
    scheme: DomainProtocol,
    tls_status: TlsStatus,
    checked_at: datetime,
) -> DomainCheckResult:
    url = f"{scheme.value}://{domain_name}"

    t0 = time.perf_counter()
    response = await client.get(url)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    status, error_text = _classify_http_status(response.status_code)

    return DomainCheckResult(
        domain_name=domain_name,
        checked_at=checked_at,
        status=status,
        scheme_used=scheme,
        tls_status=tls_status,
        http_status_code=response.status_code,
        latency_ms=latency_ms,
        error_text=error_text,
        attempt_count=1,  # overwritten by caller after retry
    )


async def _probe_scheme(
    client: httpx.AsyncClient,
    *,
    domain_name: str,
    scheme: DomainProtocol,
    tls_status: TlsStatus,
    checked_at: datetime,
) -> tuple[DomainCheckResult | None, BaseException | None, int, bool]:
    """
    Returns: (result, last_exc, attempts, tls_failed)
    Exactly one of result/last_exc will be non-None.
    """
    try:
        retry_result = await retry_async(
            lambda: _single_probe(
                client,
                domain_name=domain_name,
                scheme=scheme,
                tls_status=tls_status,
                checked_at=checked_at,
            ),
            max_attempts=MonitoringConfig.CHECKER_MAX_RETRIES,
            base_delay=MonitoringConfig.CHECKER_RETRY_BASE_DELAY,
            max_delay=MonitoringConfig.CHECKER_RETRY_MAX_DELAY,
            retry_if=_is_retryable,
            jitter=True,
        )
        return (
            replace(retry_result.value, attempt_count=retry_result.attempts),
            None,
            retry_result.attempts,
            False,
        )

    except RetryExhausted as exc:
        return None, exc.last_exc, exc.attempts, _is_tls_error(exc.last_exc)

    except Exception as exc:
        logger.exception(
            "Unexpected probe error domain=%r scheme=%r",
            domain_name,
            scheme,
        )
        return None, exc, 1, False


async def probe_domain(
    domain_name: str,
    client: httpx.AsyncClient,
) -> DomainCheckResult:
    """
    Probe *domain_name*, trying HTTPS first and falling back to HTTP.
    Always returns a DomainCheckResult — never raises.
    """
    assert client is not None
    return await _probe_with_client(domain_name, client)


async def _probe_with_client(
    domain_name: str,
    client: httpx.AsyncClient,
) -> DomainCheckResult:
    checked_at = datetime.now(tz=timezone.utc)

    https_result, https_exc, https_attempts, https_tls_failed = await _probe_scheme(
        client,
        domain_name=domain_name,
        scheme=DomainProtocol.https,
        tls_status=TlsStatus.valid,
        checked_at=checked_at,
    )

    if https_result is not None:
        return https_result

    # HTTPS failed — try plain HTTP as fallback
    http_result, http_exc, http_attempts, _ = await _probe_scheme(
        client,
        domain_name=domain_name,
        scheme=DomainProtocol.http,
        tls_status=TlsStatus.not_checked,
        checked_at=checked_at,
    )

    total_attempts = https_attempts + http_attempts

    if http_result is not None:
        if https_tls_failed:
            # Reachable over HTTP but TLS is broken -> degraded
            return replace(
                http_result,
                status=MonitorStatus.degraded,
                tls_status=TlsStatus.invalid,
                error_text=(
                    _combine_errors(https_exc, None)
                    or "HTTPS TLS verification failed; HTTP fallback succeeded."
                ),
                attempt_count=total_attempts,
            )
        return replace(http_result, attempt_count=total_attempts)

    # Both HTTPS and HTTP failed
    return DomainCheckResult(
        domain_name=domain_name,
        checked_at=checked_at,
        status=MonitorStatus.down,
        scheme_used=None,
        tls_status=TlsStatus.invalid if https_tls_failed else TlsStatus.not_checked,
        http_status_code=None,
        latency_ms=None,
        error_text=_combine_errors(https_exc, http_exc),
        attempt_count=total_attempts,
    )


def _combine_errors(
    https_exc: BaseException | None,
    http_exc: BaseException | None,
) -> str | None:
    parts = []
    if https_exc is not None:
        parts.append(f"HTTPS: {type(https_exc).__name__}: {https_exc}")
    if http_exc is not None:
        parts.append(f"HTTP: {type(http_exc).__name__}: {http_exc}")
    return "; ".join(parts) or None
