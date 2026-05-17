import httpx

from domain_monitoring.monitoring.config import MonitoringConfig


def build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        follow_redirects=True,
        verify=True,
        timeout=httpx.Timeout(
            connect=MonitoringConfig.CONNECT_TIMEOUT,
            read=MonitoringConfig.READ_TIMEOUT,
            write=5.0,
            pool=5.0,
        ),
        headers={"User-Agent": MonitoringConfig.USER_AGENT_HEADER},
    )
