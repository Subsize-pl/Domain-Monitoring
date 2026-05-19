import asyncio
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from domain_monitoring.core.utils.log.logger import get_logger
from domain_monitoring.monitoring.config import MonitoringConfig
from domain_monitoring.monitoring.core.worker_pool import DomainCheckWorkerPool
from domain_monitoring.monitoring.repositories.domain import DomainRepository
from domain_monitoring.monitoring.utils import build_bucket_started_at

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


logger = get_logger(__name__)


class DomainCheckScheduler:
    """
    Ties APScheduler to the worker pool.

    Every CHECK_INTERVAL_SECONDS the scheduler fires _run_cycle(), which:
      1. Loads all enabled domains in a short read-only session.
      2. Pushes them into the worker pool.
      3. Waits for the pool to drain (probe + write queues both empty).
    """

    def __init__(
        self,
        *,
        session_factory: "async_sessionmaker[AsyncSession]",
    ) -> None:
        self._session_factory = session_factory
        self._pool = DomainCheckWorkerPool(
            session_factory=session_factory,
            probe_workers=MonitoringConfig.WORKERS_POOL_PROBE_WORKERS_COUNT,
            writer_workers=MonitoringConfig.WORKERS_POOL_WRITER_WORKERS_COUNT,
            probe_queue_size=MonitoringConfig.WORKERS_POOL_PROBE_QUEUE_SIZE,
            write_queue_size=MonitoringConfig.WORKERS_POOL_WRITE_QUEUE_SIZE,
        )
        self._scheduler = AsyncIOScheduler()
        self._cycle_lock = asyncio.Lock()

        self._scheduler.add_job(
            self._run_cycle,
            trigger=CronTrigger(
                minute="*/5",
                second=0,
                timezone=timezone.utc,
            ),
            id=MonitoringConfig.SCHEDULER_ID,
            name=MonitoringConfig.SCHEDULER_NAME,
            max_instances=MonitoringConfig.SCHEDULER_MAX_INSTANCES,
            coalesce=MonitoringConfig.SCHEDULER_COALESCE,
            misfire_grace_time=MonitoringConfig.SCHEDULER_MISFIRE_GRACE_SECONDS,
            replace_existing=True,
        )

    async def start(self) -> None:
        await self._pool.start()
        self._scheduler.start()
        logger.info(
            "%s started: interval=%ss probe_workers=%d writer_workers=%d",
            MonitoringConfig.SCHEDULER_NAME,
            MonitoringConfig.CHECK_INTERVAL_SECONDS,
            MonitoringConfig.WORKERS_POOL_PROBE_WORKERS_COUNT,
            MonitoringConfig.WORKERS_POOL_WRITER_WORKERS_COUNT,
        )

    async def stop(self) -> None:
        self._scheduler.shutdown(wait=False)

        # Acquire the lock to wait for any in-progress _run_cycle to finish
        async with self._cycle_lock:
            pass

        await self._pool.stop()
        logger.info(
            "%s stopped.",
            MonitoringConfig.SCHEDULER_NAME,
        )

    async def _run_cycle(self) -> None:
        async with self._cycle_lock:
            bucket_started_at = build_bucket_started_at()

            async with self._session_factory() as session:
                domains = list(
                    await DomainRepository(session).get_all_enabled_domains(),
                )

            if not domains:
                logger.debug("No enabled domains. Skipping check cycle.")
                return

            logger.info(
                "Check cycle started for %d domain(s), bucket=%s",
                len(domains),
                bucket_started_at,
            )

            await self._pool.enqueue_domains(
                domains,
                bucket_started_at=bucket_started_at,
            )
            await self._pool.join()

            logger.info(
                "Check cycle finished for %d domain(s), bucket=%s",
                len(domains),
                bucket_started_at,
            )
