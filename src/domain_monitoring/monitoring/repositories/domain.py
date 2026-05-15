import uuid
from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain_monitoring.core.utils.log.logger import get_logger
from domain_monitoring.monitoring.models.domain import Domain
from domain_monitoring.monitoring.models.user_domain import UserDomain

logger = get_logger(__name__)


@dataclass
class TitledDomain:
    domain: Domain
    title: str


class DomainRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, domain_id: uuid.UUID) -> Domain | None:
        result = await self._session.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        domain = result.scalar_one_or_none()
        logger.debug(
            "Loaded domain by id %s: %s",
            domain_id,
            domain is not None,
        )
        return domain

    async def get_by_name(self, name: str) -> Domain | None:
        result = await self._session.execute(select(Domain).where(Domain.name == name))
        domain = result.scalar_one_or_none()
        logger.debug(
            "Loaded domain by name %s: %s",
            name,
            domain is not None,
        )
        return domain

    async def count_user_domains(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(UserDomain)
            .where(UserDomain.user_id == user_id)
        )
        return result.scalar_one()

    async def get_user_domains_paginated(
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[TitledDomain]:
        result = await self._session.execute(
            select(Domain, UserDomain.title)
            .join(UserDomain, UserDomain.domain_id == Domain.id)
            .where(
                UserDomain.user_id == user_id,
                Domain.is_archived.is_(False),
            )
            .order_by(Domain.created_at.desc(), Domain.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [TitledDomain(domain=d, title=t) for d, t in result.all()]

    async def get_user_domain_link(
        self,
        user_id: uuid.UUID,
        domain_id: uuid.UUID,
    ) -> UserDomain | None:
        result = await self._session.execute(
            select(UserDomain).where(
                UserDomain.user_id == user_id,
                UserDomain.domain_id == domain_id,
            )
        )
        link = result.scalar_one_or_none()
        logger.debug(
            "Loaded user-domain link for user %s and domain %s: %s",
            user_id,
            domain_id,
            link is not None,
        )
        return link

    async def get_all_enabled_domains(self) -> Sequence[Domain]:
        result = await self._session.execute(
            select(Domain).where(
                Domain.is_enabled.is_(True),
                Domain.is_archived.is_(False),
            )
        )
        domains = result.scalars().all()
        logger.debug(
            "Loaded %s enabled domains",
            len(domains),
        )
        return domains

    async def create_domain(self, name: str) -> Domain:
        domain = Domain(name=name)
        self._session.add(domain)
        await self._session.flush()
        logger.info(
            "Created domain %s (%s)",
            domain.name,
            domain.id,
        )
        return domain

    async def create_user_domain_link(
        self,
        user_id: uuid.UUID,
        domain_id: uuid.UUID,
        title: str | None = None,
    ) -> UserDomain:
        link = UserDomain(
            user_id=user_id,
            domain_id=domain_id,
            title=title,
        )
        self._session.add(link)
        await self._session.flush()
        logger.info(
            "Created user-domain link for user %s and domain %s %s",
            user_id,
            domain_id,
            f"with title {title!r}" if title is not None else "without title",
        )
        return link

    async def remove_user_domain_link(
        self,
        user_id: uuid.UUID,
        domain_id: uuid.UUID,
    ):
        await self._session.execute(
            delete(UserDomain).where(
                UserDomain.user_id == user_id,
                UserDomain.domain_id == domain_id,
            )
        )

    async def archive_domain_if_orphan(self, domain_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(func.count())
            .select_from(UserDomain)
            .where(UserDomain.domain_id == domain_id)
        )
        if result.scalar_one() != 0:
            logger.debug(
                "Domain %s is still linked to users",
                domain_id,
            )
            return False

        domain = await self.get_by_id(domain_id)
        if domain is None:
            logger.debug(
                "Domain %s was not found for orphan archive",
                domain_id,
            )
            return False

        if domain.is_archived and not domain.is_enabled:
            logger.debug("Domain %s is already archived", domain_id)
            return False

        domain.is_archived = True
        domain.is_enabled = False
        await self._session.flush()
        logger.info(
            "Archived orphan domain %s (%s)",
            domain.name,
            domain.id,
        )
        return True
