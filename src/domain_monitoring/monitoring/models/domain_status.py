from enum import Enum


class MonitorStatus(str, Enum):
    unknown = "unknown"
    up = "up"
    degraded = "degraded"
    down = "down"
