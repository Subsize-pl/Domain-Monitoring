from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain_monitoring.infrastructure.db.db_manager import get_db_manager
from domain_monitoring.monitoring.services.domain import DomainService

db_manager = get_db_manager()


def get_domain_service(
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
) -> DomainService:
    return DomainService(session)
