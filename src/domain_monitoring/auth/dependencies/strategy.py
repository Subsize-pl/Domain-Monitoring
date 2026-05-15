from fastapi import Depends

from domain_monitoring.auth.backend.strategy import SessionStrategy
from domain_monitoring.auth.dependencies.session_service import get_auth_session_service
from domain_monitoring.auth.services import AuthSessionService


def get_session_strategy(
    service: AuthSessionService = Depends(get_auth_session_service),
) -> SessionStrategy:
    return SessionStrategy(service)
