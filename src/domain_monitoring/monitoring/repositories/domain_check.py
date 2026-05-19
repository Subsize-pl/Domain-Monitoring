import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from domain_monitoring.core.utils.log.logger import get_logger
from domain_monitoring.monitoring.config import MonitoringConfig
from domain_monitoring.monitoring.models.domain_check import DomainCheck
from domain_monitoring.monitoring.models.domain_protocol import DomainProtocol
from domain_monitoring.monitoring.models.monitor_status import MonitorStatus
from domain_monitoring.monitoring.models.tls_status import TlsStatus
from domain_monitoring.monitoring.utils import build_bucket_started_at

logger = get_logger(__name__)


class DomainCheckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _validate_timeline_params(
        self,
        *,
        limit_per_domain: int,
        window_intervals: int,
    ) -> None:
        if limit_per_domain < 0:
            raise ValueError("limit_per_domain must be >= 0")

        if limit_per_domain > MonitoringConfig.RECENT_CHECKS_LIMIT_MAX:
            raise ValueError(
                f"limit_per_domain must be <= {MonitoringConfig.RECENT_CHECKS_LIMIT_MAX}"
            )

        if window_intervals < MonitoringConfig.RECENT_CHECKS_WINDOW_INTERVALS_MIN:
            raise ValueError(
                "window_intervals must be >= "
                f"{MonitoringConfig.RECENT_CHECKS_WINDOW_INTERVALS_MIN}"
            )

        if window_intervals > MonitoringConfig.RECENT_CHECKS_WINDOW_INTERVALS_MAX:
            raise ValueError(
                "window_intervals must be <= "
                f"{MonitoringConfig.RECENT_CHECKS_WINDOW_INTERVALS_MAX}"
            )

    def _build_bucket_starts(
        self,
        *,
        limit_per_domain: int,
        window_intervals: int,
    ) -> list[datetime]:
        """
        Build fixed timeline buckets aligned to the current scheduler bucket.
        """
        bucket_started_at = build_bucket_started_at()

        interval_seconds = MonitoringConfig.CHECK_INTERVAL_SECONDS
        step_seconds = interval_seconds * window_intervals

        return [
            bucket_started_at - timedelta(seconds=step_seconds * offset)
            for offset in reversed(range(limit_per_domain))
        ]

    async def create(
        self,
        *,
        domain_id: uuid.UUID,
        bucket_started_at: datetime,
        checked_at: datetime,
        status: MonitorStatus,
        attempt_count: int,
        scheme_used: DomainProtocol | None = None,
        tls_status: TlsStatus | None = None,
        http_status_code: int | None = None,
        latency_ms: int | None = None,
        error_text: str | None = None,
    ) -> DomainCheck:
        check = DomainCheck(
            domain_id=domain_id,
            bucket_started_at=bucket_started_at,
            checked_at=checked_at,
            status=status,
            attempt_count=attempt_count,
            scheme_used=scheme_used,
            tls_status=tls_status,
            http_status_code=http_status_code,
            latency_ms=latency_ms,
            error_text=error_text,
        )
        self._session.add(check)
        await self._session.flush()
        logger.info("Created domain check: %s", check)
        return check

    async def get_latest_for_domain(
        self,
        domain_id: uuid.UUID,
        *,
        limit_per_domain: int = MonitoringConfig.RECENT_CHECKS_LIMIT_DEFAULT,
        window_intervals: int = MonitoringConfig.RECENT_CHECKS_WINDOW_INTERVALS_DEFAULT,
    ) -> list[DomainCheck | None]:
        timelines = await self.get_latest_for_domains(
            [domain_id],
            limit_per_domain=limit_per_domain,
            window_intervals=window_intervals,
        )
        return timelines[domain_id]

    async def get_latest_for_domains(
        self,
        domain_ids: list[uuid.UUID],
        *,
        limit_per_domain: int = MonitoringConfig.RECENT_CHECKS_LIMIT_DEFAULT,
        window_intervals: int = MonitoringConfig.RECENT_CHECKS_WINDOW_INTERVALS_DEFAULT,
    ) -> dict[uuid.UUID, list[DomainCheck | None]]:
        """
        Return fixed-length timelines for many domains.

        Each domain gets exactly *limit_per_domain* points.
        Points are ordered from oldest to newest.
        Missing buckets are represented as None.
        """
        if not domain_ids:
            return {}

        self._validate_timeline_params(
            limit_per_domain=limit_per_domain,
            window_intervals=window_intervals,
        )

        if limit_per_domain == 0:
            return {domain_id: [] for domain_id in domain_ids}

        unique_domain_ids = list(dict.fromkeys(domain_ids))

        bucket_starts = self._build_bucket_starts(
            limit_per_domain=limit_per_domain,
            window_intervals=window_intervals,
        )

        bucket_start_to_index: dict[datetime, int] = {
            bucket_start: index for index, bucket_start in enumerate(bucket_starts)
        }

        oldest_bucket_start = bucket_starts[0]
        newest_bucket_end = bucket_starts[-1] + timedelta(
            seconds=MonitoringConfig.CHECK_INTERVAL_SECONDS,
        )

        # Rank checks inside each (domain_id, bucket_started_at) pair.
        # rn = 1 means the newest check inside that bucket.
        ranked_checks = (
            select(
                DomainCheck,
                func.row_number()
                .over(
                    partition_by=(
                        DomainCheck.domain_id,
                        DomainCheck.bucket_started_at,
                    ),
                    order_by=(
                        DomainCheck.checked_at.desc(),
                        DomainCheck.id.desc(),
                    ),
                )
                .label("rn"),
            )
            .where(
                DomainCheck.domain_id.in_(unique_domain_ids),
                DomainCheck.bucket_started_at.in_(bucket_starts),
                DomainCheck.checked_at >= oldest_bucket_start,
                DomainCheck.checked_at < newest_bucket_end,
            )
            .subquery()
        )

        check_alias = aliased(DomainCheck, ranked_checks)

        result = await self._session.execute(
            select(check_alias).where(ranked_checks.c.rn == 1)
        )

        grouped: dict[uuid.UUID, list[DomainCheck | None]] = {
            domain_id: [None] * limit_per_domain for domain_id in unique_domain_ids
        }

        for check in result.scalars().all():
            idx = bucket_start_to_index.get(check.bucket_started_at)
            if idx is None:
                continue

            grouped[check.domain_id][idx] = check

        logger.debug(
            "Loaded timeline for %s domains with limit=%s window_intervals=%s",
            len(unique_domain_ids),
            limit_per_domain,
            window_intervals,
        )
        return grouped
