import logging
import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from monitoring.config import MonitoringConfig
from monitoring.models.domain_check import DomainCheck
from monitoring.models.domain_status import MonitorStatus

logger = logging.getLogger(__name__)


class DomainCheckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        domain_id: uuid.UUID,
        checked_at: datetime,
        status: MonitorStatus,
        http_status_code: int | None = None,
        latency_ms: int | None = None,
        error_text: str | None = None,
    ) -> DomainCheck:
        check = DomainCheck(
            domain_id=domain_id,
            checked_at=checked_at,
            status=status,
            http_status_code=http_status_code,
            latency_ms=latency_ms,
            error_text=error_text,
        )
        self._session.add(check)
        await self._session.flush()
        logger.info(
            "Created domain check for domain %s (%s)",
            domain_id,
            check.id,
        )
        return check

    async def get_latest_for_domain(
        self,
        domain_id: uuid.UUID,
        limit: int = 3,
    ) -> Sequence[DomainCheck]:
        result = await self._session.execute(
            select(DomainCheck)
            .where(DomainCheck.domain_id == domain_id)
            .order_by(DomainCheck.checked_at.desc(), DomainCheck.id.desc())
            .limit(limit)
        )
        checks = result.scalars().all()
        logger.debug(
            "Loaded %s latest checks for domain %s",
            len(checks),
            domain_id,
        )
        return checks

    async def get_latest_for_domains(
        self,
        domain_ids: list[uuid.UUID],
        limit_per_domain: int = MonitoringConfig.DEFAULT_LIMIT_PER_DOMAIN,
    ) -> dict[uuid.UUID, list[DomainCheck]]:
        if not domain_ids:
            return {}

        row_number = (
            func.row_number()
            .over(
                partition_by=DomainCheck.domain_id,
                order_by=(DomainCheck.checked_at.desc(), DomainCheck.id.desc()),
            )
            .label("rn")
        )

        ranked_checks = (
            select(
                DomainCheck,
                row_number,
            )
            .where(DomainCheck.domain_id.in_(domain_ids))
            .subquery()
        )

        check_alias = aliased(DomainCheck, ranked_checks)

        result = await self._session.execute(
            select(check_alias).where(ranked_checks.c.rn <= limit_per_domain)
        )
        checks = result.scalars().all()

        grouped: dict[uuid.UUID, list[DomainCheck]] = {
            domain_id: [] for domain_id in domain_ids
        }
        for check in checks:
            grouped[check.domain_id].append(check)

        for items in grouped.values():
            items.sort(
                key=lambda item: (item.checked_at, item.id),
                reverse=True,
            )

        logger.debug(
            "Loaded latest checks for %s domains with limit %s",
            len(domain_ids),
            limit_per_domain,
        )
        return grouped
