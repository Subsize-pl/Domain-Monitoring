import uuid
import redis.asyncio as redis
import logging

from .keys import AuthRedisKeys

logger = logging.getLogger(__name__)


class AuthSessionCache:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        self.keys = AuthRedisKeys()
        logger.debug(f"Initialized AuthSessionCache with redis URL: {self.redis_url}")

    async def get_user_id(self, session_id: uuid.UUID) -> uuid.UUID:
        try:
            logger.debug(f"Getting user ID for session: {session_id}")
            user_id = await self.redis.get(self.keys.session_user(session_id))
            if user_id:
                logger.debug(f"User ID {user_id} found for session {session_id}")
            else:
                logger.warning(f"No user ID found for session {session_id}")
            return user_id
        except Exception as e:
            logger.error(f"Error retrieving user ID for session {session_id}: {e}")
            raise

    async def cache_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID, ttl: int
    ) -> None:
        try:
            logger.debug(
                f"Caching session {session_id} for user {user_id} with TTL {ttl}"
            )
            pipe = self.redis.pipeline(transaction=False)
            pipe.set(self.keys.session_user(session_id), str(user_id), ex=ttl)
            pipe.sadd(self.keys.user_sessions(user_id), str(session_id))
            await pipe.execute()
            logger.info(f"Session {session_id} cached for user {user_id}")
        except Exception as e:
            logger.error(f"Error caching session {session_id} for user {user_id}: {e}")
            raise

    async def delete_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> None:
        try:
            logger.debug(f"Deleting session {session_id}")
            pipe = self.redis.pipeline(transaction=False)
            pipe.delete(self.keys.session_user(session_id))
            if user_id is not None:
                pipe.srem(self.keys.user_sessions(user_id), str(session_id))
            await pipe.execute()
            logger.info(f"Session {session_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            raise

    async def delete_user_sessions(
        self, user_id: uuid.UUID, session_ids: list[uuid.UUID]
    ) -> None:
        try:
            logger.debug(f"Deleting sessions for user {user_id}")
            pipe = self.redis.pipeline(transaction=False)
            if session_ids:
                pipe.delete(*(self.keys.session_user(sid) for sid in session_ids))
            pipe.delete(self.keys.user_sessions(user_id))
            await pipe.execute()
            logger.info(f"All sessions for user {user_id} deleted")
        except Exception as e:
            logger.error(f"Error deleting sessions for user {user_id}: {e}")
            raise
