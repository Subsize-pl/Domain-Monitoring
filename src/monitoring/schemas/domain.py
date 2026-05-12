import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from monitoring.config import MonitoringConfig
from monitoring.models.domain_status import MonitorStatus


class DomainAddRequest(BaseModel):
    name: str
    title: Annotated[
        str,
        Field(max_length=MonitoringConfig.MAX_DOMAIN_TITLE_LENGTH),
    ]

    model_config = {
        "extra": "forbid",
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }


class DomainCheckOut(BaseModel):
    id: uuid.UUID
    checked_at: datetime
    status: MonitorStatus
    http_status_code: int | None
    latency_ms: int | None
    error_text: str | None

    model_config = {"from_attributes": True}


class DomainOut(BaseModel):
    id: uuid.UUID
    name: str
    title: str
    is_enabled: bool
    created_at: datetime
    # Last 3 checks (newest first)
    latest_checks: list[DomainCheckOut] = []

    model_config = {"from_attributes": True}


class DomainListOut(BaseModel):
    domains: list[DomainOut]
    total: int
    page: int
    page_size: int
    pages: int
