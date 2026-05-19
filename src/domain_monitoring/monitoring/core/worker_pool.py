import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

import httpx

from domain_monitoring.core.utils.log.logger import get_logger
from domain_monitoring.monitoring.core.checker import DomainCheckResult, probe_domain
from domain_monitoring.monitoring.dependencies.httpx_async_client import build_client
from domain_monitoring.monitoring.models.domain import Domain
from domain_monitoring.monitoring.repositories.domain_check import DomainCheckRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

logger = get_logger(__name__)


class DomainCheckWorkerPool:
    """
    Producer/consumer pool for domain checks.

    Probe workers pull (Domain, bucket_started_at) jobs from the probe queue,
    call probe_domain, and push (Domain, bucket_started_at, result) records to
    the write queue.

    Writer workers persist each result in its own short-lived DB transaction.
    """

    def __init__(
        self,
        *,
        session_factory: "async_sessionmaker[AsyncSession]",
        probe_workers: int,
        writer_workers: int,
        probe_queue_size: int,
        write_queue_size: int,
    ) -> None:
        self._session_factory = session_factory
        self._probe_workers_cnt = probe_workers
        self._writer_workers_cnt = writer_workers

        self._probe_queue: asyncio.Queue[tuple[Domain, datetime] | None] = (
            asyncio.Queue(maxsize=probe_queue_size)
        )
        self._write_queue: asyncio.Queue[
            tuple[Domain, datetime, DomainCheckResult] | None
        ] = asyncio.Queue(maxsize=write_queue_size)

        self._probe_tasks: list[asyncio.Task[None]] = []
        self._writer_tasks: list[asyncio.Task[None]] = []
        self._client: httpx.AsyncClient | None = None
        self._started = False

    async def start(self) -> None:
        if self._started:
            return

        self._client = build_client()

        self._probe_tasks = [
            asyncio.create_task(
                self._probe_worker(i),
                name=f"probe-worker-{i}",
            )
            for i in range(self._probe_workers_cnt)
        ]
        self._writer_tasks = [
            asyncio.create_task(
                self._writer_worker(i),
                name=f"writer-worker-{i}",
            )
            for i in range(self._writer_workers_cnt)
        ]
        self._started = True
        logger.info(
            "Worker pool started: probe_workers=%d writer_workers=%d",
            self._probe_workers_cnt,
            self._writer_workers_cnt,
        )

    async def stop(self) -> None:
        if not self._started:
            return

        await self.join()

        for _ in self._probe_tasks:
            await self._probe_queue.put(None)
        for _ in self._writer_tasks:
            await self._write_queue.put(None)

        await asyncio.gather(*self._probe_tasks, return_exceptions=True)
        await asyncio.gather(*self._writer_tasks, return_exceptions=True)

        if self._client is not None:
            await self._client.aclose()
            self._client = None

        self._probe_tasks.clear()
        self._writer_tasks.clear()
        self._started = False
        logger.info("Worker pool stopped.")

    async def enqueue_domains(
        self,
        domains: list[Domain],
        *,
        bucket_started_at: datetime,
    ) -> None:
        if not self._started:
            raise RuntimeError("Worker pool is not running.")
        for domain in domains:
            await self._probe_queue.put((domain, bucket_started_at))

    async def join(self) -> None:
        await self._probe_queue.join()
        await self._write_queue.join()

    async def _probe_worker(self, worker_id: int) -> None:
        assert self._client is not None

        while True:
            item = await self._probe_queue.get()
            try:
                if item is None:
                    return

                domain, bucket_started_at = item
                result = await probe_domain(domain.name, client=self._client)
                await self._write_queue.put((domain, bucket_started_at, result))

            except Exception:
                domain_name = item[0].name
                logger.exception(
                    "Probe worker error domain=%r worker=%d",
                    getattr(domain_name, "name", "?"),
                    worker_id,
                )
            finally:
                self._probe_queue.task_done()

    async def _writer_worker(self, worker_id: int) -> None:
        while True:
            item = await self._write_queue.get()
            try:
                if item is None:
                    return

                domain, bucket_started_at, result = item
                await self._persist(
                    domain=domain,
                    bucket_started_at=bucket_started_at,
                    result=result,
                    worker_id=worker_id,
                )

            except Exception:
                logger.exception(
                    "Writer worker unhandled error worker=%d",
                    worker_id,
                )
            finally:
                self._write_queue.task_done()

    async def _persist(
        self,
        *,
        domain: Domain,
        bucket_started_at: datetime,
        result: DomainCheckResult,
        worker_id: int,
    ) -> None:
        async with self._session_factory() as session:
            check_domain_orm = await DomainCheckRepository(session).create(
                domain_id=domain.id,
                bucket_started_at=bucket_started_at,
                checked_at=result.checked_at,
                status=result.status,
                http_status_code=result.http_status_code,
                latency_ms=result.latency_ms,
                error_text=result.error_text,
                attempt_count=result.attempt_count,
                scheme_used=result.scheme_used,
                tls_status=result.tls_status,
            )
            await session.commit()

        logger.debug(
            "Worker=%d: stored check domain=%r bucket=%s result=%s",
            worker_id,
            domain.name,
            bucket_started_at,
            check_domain_orm,
        )
