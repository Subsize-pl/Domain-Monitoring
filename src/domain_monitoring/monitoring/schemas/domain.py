import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from domain_monitoring.core.utils.domain_validation import MAXIMUM_DOMAIN_LENGTH
from domain_monitoring.monitoring.config import MonitoringConfig
from domain_monitoring.monitoring.models.domain_protocol import DomainProtocol
from domain_monitoring.monitoring.models.monitor_status import MonitorStatus
from domain_monitoring.monitoring.models.tls_status import TlsStatus


class DomainAddRequest(BaseModel):
    name: Annotated[
        str,
        Field(max_length=MAXIMUM_DOMAIN_LENGTH),
    ]
    title: Annotated[
        str | None,
        Field(
            default=None,
            max_length=MonitoringConfig.MAX_DOMAIN_TITLE_LENGTH,
        ),
    ]

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }


class DomainCheckOut(BaseModel):
    id: uuid.UUID
    checked_at: datetime
    bucket_started_at: datetime
    status: MonitorStatus
    scheme_used: DomainProtocol | None
    tls_status: TlsStatus
    http_status_code: int | None
    latency_ms: int | None
    error_text: str | None

    model_config = {"from_attributes": True}


class DomainOut(BaseModel):
    id: uuid.UUID
    name: str
    title: str | None
    is_enabled: bool
    latest_checks: list[DomainCheckOut | None] = []

    model_config = {"from_attributes": True}


class DomainListOut(BaseModel):
    domains: list[DomainOut]
    total: int
    page: int
    page_size: int
    pages: int
