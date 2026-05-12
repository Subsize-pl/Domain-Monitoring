from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.db_manager import db_manager
from monitoring.services.domain import DomainService


def get_domain_service(
    session: Annotated[AsyncSession, Depends(db_manager.get_session)],
) -> DomainService:
    return DomainService(session)
