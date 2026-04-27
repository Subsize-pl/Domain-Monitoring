import uuid
from datetime import timedelta
from auth.cache.session import AuthSessionCache
from auth.repositories.session import AuthSessionRepository
from auth.utils import utc_now
from core.utils.log.logger import get_logger

logger = get_logger(__name__)


class AuthSessionService:
    def __init__(
        self,
        cache: AuthSessionCache,
        repo: AuthSessionRepository,
        session_ttl: int,
    ) -> None:
        self.cache = cache
        self.repo = repo
        self.session_ttl = session_ttl

    async def create_session(self, user_id: uuid.UUID) -> str:
        logger.info(f"Creating session for user {user_id}")
        session_id = uuid.uuid4()
        now = utc_now()
        expires_at = now + timedelta(seconds=self.session_ttl)

        await self.repo.add(session_id, user_id, expires_at)
        logger.info(
            f"Session {session_id} created for user {user_id}, expires at {expires_at}"
        )

        try:
            await self.cache.cache_session(session_id, user_id, self.session_ttl)
            logger.info(f"Session {session_id} cached for user {user_id}")
        except Exception as e:
            logger.error(
                f"Failed to cache session {session_id} for user {user_id}: {str(e)}"
            )
            await self.repo.revoke(session_id, now)
            logger.info(f"Session {session_id} revoked due to cache failure.")
            raise

        return str(session_id)

    async def get_user_id_by_session_id(self, session_id: str) -> uuid.UUID | None:
        session_uuid = uuid.UUID(session_id)
        logger.info(f"Getting user ID for session {session_uuid}")

        cached_user_id = await self.cache.get_user_id(session_uuid)
        if cached_user_id is not None:
            logger.info(
                f"Found user ID {cached_user_id} in cache for session {session_uuid}"
            )
            return cached_user_id

        row = await self.repo.get_user_id_and_expires_at(session_uuid)
        if not row:
            logger.warning(f"Session {session_uuid} not found in database.")
            return None

        user_id, expires_at = row
        now = utc_now()

        if expires_at <= now:
            logger.warning(f"Session {session_uuid} expired at {expires_at}.")
            return None

        ttl = max(int((expires_at - now).total_seconds()), 1)
        await self.cache.cache_session(session_uuid, user_id, ttl)
        logger.info(f"Session {session_uuid} cached for user {user_id} with ttl {ttl}")

        return user_id

    async def revoke_session(self, session_id: str) -> None:
        session_uuid = uuid.UUID(session_id)
        now = utc_now()
        logger.info(f"Revoking session {session_uuid}")

        cached_user_id = await self.cache.get_user_id(session_uuid)
        if cached_user_id is not None:
            user_id = cached_user_id
            logger.info(f"Found cached user ID {user_id} for session {session_uuid}")
        else:
            user_id = await self.repo.get_user_id(session_uuid)
            logger.info(
                f"Found user ID {user_id} in database for session {session_uuid}"
            )

        await self.cache.delete_session(
            session_uuid,
            user_id if user_id else None,
        )
        await self.repo.revoke(session_uuid, now)
        logger.info(f"Session {session_uuid} revoked.")

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> None:
        logger.info(f"Revoking all sessions for user {user_id}")
        now = utc_now()

        session_ids = await self.repo.get_active_session_ids(user_id)
        await self.cache.delete_user_sessions(user_id, list(session_ids))
        logger.info(
            f"Deleted {len(session_ids)} sessions from cache for user {user_id}"
        )

        await self.repo.revoke_all_for_user(user_id, now)
        logger.info(f"Revoked all sessions for user {user_id} in database.")
