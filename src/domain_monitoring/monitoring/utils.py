from datetime import timezone, datetime

from domain_monitoring.monitoring.config import MonitoringConfig


def build_bucket_started_at() -> datetime:
    interval_seconds = MonitoringConfig.CHECK_INTERVAL_SECONDS
    now = datetime.now(timezone.utc)
    bucket_ts = int(now.timestamp() // interval_seconds) * interval_seconds
    return datetime.fromtimestamp(bucket_ts, tz=timezone.utc)
