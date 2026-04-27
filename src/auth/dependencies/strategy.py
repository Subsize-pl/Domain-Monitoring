from fastapi import Depends

from auth.backend.strategy import SessionStrategy
from auth.dependencies.session_service import get_auth_session_service
from auth.services import AuthSessionService


def get_session_strategy(
    service: AuthSessionService = Depends(get_auth_session_service),
) -> SessionStrategy:
    return SessionStrategy(service)
