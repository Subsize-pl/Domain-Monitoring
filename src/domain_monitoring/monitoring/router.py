import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from domain_monitoring.core.exceptions.domain_validation import (
    DomainValidationException,
)
from domain_monitoring.core.utils.log.logger import get_logger
from domain_monitoring.auth import get_current_active_user
from domain_monitoring.auth.models import User
from domain_monitoring.monitoring.config import MonitoringConfig
from domain_monitoring.monitoring.dependencies.domain_service import get_domain_service

from domain_monitoring.monitoring.schemas.domain import (
    DomainAddRequest,
    DomainOut,
    DomainListOut,
)
from domain_monitoring.monitoring.services.domain import (
    DomainService,
)
from domain_monitoring.monitoring.exceptions import (
    DomainLimitExceeded,
    DomainNotFound,
    DomainAlreadyAdded,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix=MonitoringConfig.ROUTER_PREFIX,
    tags=[MonitoringConfig.ROUTER_TAG],
)


@router.get(
    "/",
    response_model=DomainListOut,
    summary="List monitored domains with recent check statuses",
)
async def list_domains(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[DomainService, Depends(get_domain_service)],
) -> DomainListOut:
    return await service.list_domains(current_user.id)


@router.post(
    "/",
    response_model=DomainOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a domain to your monitoring list",
)
async def add_domain(
    body: DomainAddRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[DomainService, Depends(get_domain_service)],
) -> DomainOut:
    try:
        return await service.add_domain(current_user.id, body.name)
    except DomainLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )
    except DomainAlreadyAdded as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except DomainValidationException as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete(
    "/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a domain from your monitoring list",
)
async def remove_domain(
    domain_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[DomainService, Depends(get_domain_service)],
) -> None:
    try:
        await service.remove_domain(current_user.id, domain_id)
    except DomainNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
