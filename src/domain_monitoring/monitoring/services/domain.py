import math
import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from domain_monitoring.core.utils.log.logger import get_logger
from domain_monitoring.monitoring.config import MonitoringConfig
from domain_monitoring.monitoring.exceptions import (
    DomainLimitExceeded,
    DomainNotFound,
    DomainAlreadyAdded,
)
from domain_monitoring.monitoring.models import DomainCheck
from domain_monitoring.monitoring.models.domain import Domain
from domain_monitoring.monitoring.repositories.domain import (
    DomainRepository,
    TitledDomain,
)
from domain_monitoring.monitoring.repositories.domain_check import (
    DomainCheckRepository,
)
from domain_monitoring.monitoring.schemas.domain import (
    DomainCheckOut,
    DomainListOut,
    DomainOut,
)
from domain_monitoring.core.utils.domain_validation import (
    normalize_and_validate_domain,
)
from domain_monitoring.core.exceptions.domain_validation import (
    DomainValidationException,
)

logger = get_logger(__name__)


class DomainService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._domain_repo = DomainRepository(session)
        self._check_repo = DomainCheckRepository(session)

    async def add_domain(
        self,
        user_id: uuid.UUID,
        name: str,
        title: str | None = None,
    ) -> DomainOut:
        try:
            logger.debug(
                "Normalizing and validating domain name %r",
                name,
            )
            normalized = normalize_and_validate_domain(name).normalized
        except DomainValidationException as exc:
            logger.debug("Invalid domain name %r: %s", name, exc)
            raise
        logger.info("Adding domain %r for user %s", normalized, user_id)

        count = await self._domain_repo.count_user_domains(user_id)
        if count >= MonitoringConfig.MAX_DOMAINS_PER_USER:
            logger.warning("User %s reached the domain limit", user_id)
            raise DomainLimitExceeded(
                f"You have reached the limit of"
                f" {MonitoringConfig.MAX_DOMAINS_PER_USER} domains."
            )

        domain = await self._domain_repo.get_by_name(normalized)
        if domain is not None:
            existing_link = await self._domain_repo.get_user_domain_link(
                user_id,
                domain.id,
            )
            if existing_link is not None:
                logger.info(
                    "Domain %r is already added for user %s",
                    normalized,
                    user_id,
                )
                raise DomainAlreadyAdded(
                    f"Domain '{normalized}' is already in your list."
                )
        else:
            domain = await self._domain_repo.create_domain(normalized)

        if domain.is_archived:
            domain.is_archived = False
            domain.is_enabled = True

        await self._domain_repo.create_user_domain_link(
            user_id,
            domain.id,
            title=title,
        )

        try:
            await self._session.commit()
            await self._session.refresh(domain)
        except Exception:
            await self._session.rollback()
            logger.exception(
                "Failed to add domain %r for user %s %s",
                normalized,
                user_id,
                f"with title {title!r}" if title is not None else "without title",
            )
            raise

        return self._build_domain_out(domain, [], title=title)

    async def remove_domain(
        self,
        user_id: uuid.UUID,
        domain_id: uuid.UUID,
    ) -> None:
        logger.info("Removing domain %s for user %s", domain_id, user_id)

        link = await self._domain_repo.get_user_domain_link(
            user_id,
            domain_id,
        )
        if link is None:
            logger.warning(
                "Domain %s was not found for user %s",
                domain_id,
                user_id,
            )
            raise DomainNotFound("Domain not found in your list.")

        await self._domain_repo.remove_user_domain_link(user_id, domain_id)
        archived = await self._domain_repo.archive_domain_if_orphan(domain_id)

        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            logger.exception(
                "Failed to remove domain %s for user %s",
                domain_id,
                user_id,
            )
            raise

        if archived:
            logger.info(
                "Domain %s was archived after the last link was removed",
                domain_id,
            )

    async def list_domains(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = MonitoringConfig.DOMAIN_PAGE_SIZE_DEFAULT,
        recent_checks_limit: int = MonitoringConfig.RECENT_CHECKS_LIMIT_DEFAULT,
        recent_checks_window_intervals: int = (
            MonitoringConfig.RECENT_CHECKS_WINDOW_INTERVALS_DEFAULT,
        ),
    ) -> DomainListOut:
        page = max(page, 1)
        page_size = max(
            MonitoringConfig.DOMAIN_PAGE_SIZE_MIN,
            min(page_size, MonitoringConfig.DOMAIN_PAGE_SIZE_MAX),
        )
        offset = (page - 1) * page_size

        total = await self._domain_repo.count_user_domains(user_id)
        if total < 1:
            return DomainListOut(
                domains=[],
                total=total,
                page=page,
                page_size=page_size,
                pages=math.ceil(total / page_size) if total else 0,
            )

        titled_domains: list[TitledDomain] = (
            await self._domain_repo.get_user_domains_paginated(
                user_id,
                limit=page_size,
                offset=offset,
            )
        )

        if not titled_domains:
            return DomainListOut(
                domains=[],
                total=total,
                page=page,
                page_size=page_size,
                pages=math.ceil(total / page_size) if total else 0,
            )

        domain_ids = [t_domain.domain.id for t_domain in titled_domains]
        checks_map = await self._check_repo.get_latest_for_domains(
            domain_ids,
            limit_per_domain=recent_checks_limit,
            window_intervals=recent_checks_window_intervals,
        )

        items: list[DomainOut] = []
        for titled_domain in titled_domains:
            raw_checks: list[DomainCheck] = checks_map.get(
                titled_domain.domain.id,
                [],
            )
            items.append(
                self._build_domain_out(
                    titled_domain.domain,
                    raw_checks,
                    title=titled_domain.title,
                )
            )

        return DomainListOut(
            domains=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total else 0,
        )

    def _build_domain_out(
        self,
        domain: Domain,
        checks: Sequence[DomainCheck],
        title: str | None = None,
    ) -> DomainOut:
        return DomainOut(
            id=domain.id,
            name=domain.name,
            title=title,
            is_enabled=domain.is_enabled,
            latest_checks=[
                None if check is None else DomainCheckOut.model_validate(check)
                for check in checks
            ],
        )
