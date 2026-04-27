import uuid
from datetime import datetime
from typing import Sequence
import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models.session import AuthSession
from auth.utils import utc_now

logger = logging.getLogger(__name__)


class AuthSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        expires_at: datetime,
    ) -> None:
        try:
            logger.debug(
                f"Adding session {session_id} for user {user_id}, expires at {expires_at}"
            )
            self.session.add(
                AuthSession(id=session_id, user_id=user_id, expires_at=expires_at)
            )
            await self.session.commit()
            logger.info(f"Session {session_id} added for user {user_id}")
        except Exception as e:
            logger.error(f"Error adding session {session_id} for user {user_id}: {e}")
            raise

    async def get_user_id_and_expires_at(
        self,
        session_id: uuid.UUID,
    ) -> tuple[uuid.UUID, datetime] | None:
        try:
            logger.debug(f"Getting user_id and expires_at for session {session_id}")
            stmt = select(AuthSession.user_id, AuthSession.expires_at).where(
                AuthSession.id == session_id,
                AuthSession.revoked_at.is_(None),
            )
            result = await self.session.execute(stmt)
            user_data = result.first()
            if user_data:
                logger.debug(
                    f"Found user_id and expires_at for session {session_id}: {user_data}"
                )
            else:
                logger.warning(f"No active session found for session {session_id}")
            return user_data
        except Exception as e:
            logger.error(
                f"Error fetching user_id and expires_at for session {session_id}: {e}"
            )
            raise

    async def get_active_session_ids(
        self,
        user_id: uuid.UUID,
    ) -> Sequence[uuid.UUID]:
        try:
            logger.debug(f"Fetching active session IDs for user {user_id}")
            stmt = select(AuthSession.id).where(
                AuthSession.user_id == user_id,
                AuthSession.expires_at > utc_now(),
                AuthSession.revoked_at.is_(None),
            )
            result = await self.session.execute(stmt)
            active_sessions = result.scalars().all()
            logger.debug(f"Active sessions for user {user_id}: {active_sessions}")
            return active_sessions
        except Exception as e:
            logger.error(f"Error fetching active session IDs for user {user_id}: {e}")
            raise

    async def get_user_id(self, session_id: uuid.UUID) -> uuid.UUID | None:
        try:
            logger.debug(f"Getting user ID for session {session_id}")
            stmt = select(AuthSession.user_id).where(AuthSession.id == session_id)
            result = await self.session.execute(stmt)
            user_id = result.scalar_one_or_none()
            logger.debug(f"Found user_id for session {session_id}: {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"Error fetching user_id for session {session_id}: {e}")
            raise

    async def revoke(
        self,
        session_id: uuid.UUID,
        revoked_at: datetime,
    ) -> None:
        try:
            logger.debug(f"Revoking session {session_id} at {revoked_at}")
            await self.session.execute(
                update(AuthSession)
                .where(AuthSession.id == session_id)
                .where(AuthSession.revoked_at.is_(None))
                .values(revoked_at=revoked_at)
            )
            await self.session.commit()
            logger.info(f"Session {session_id} revoked at {revoked_at}")
        except Exception as e:
            logger.error(f"Error revoking session {session_id}: {e}")
            raise

    async def revoke_all_for_user(
        self,
        user_id: uuid.UUID,
        revoked_at: datetime,
    ) -> None:
        try:
            logger.debug(f"Revoking all sessions for user {user_id} at {revoked_at}")
            await self.session.execute(
                update(AuthSession)
                .where(AuthSession.user_id == user_id)
                .where(AuthSession.revoked_at.is_(None))
                .values(revoked_at=revoked_at)
            )
            await self.session.commit()
            logger.info(f"All sessions for user {user_id} revoked at {revoked_at}")
        except Exception as e:
            logger.error(f"Error revoking all sessions for user {user_id}: {e}")
            raise
