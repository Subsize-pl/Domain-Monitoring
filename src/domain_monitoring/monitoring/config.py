class MonitoringConfig:
    ROUTER_PREFIX = "/domains"
    ROUTER_TAG = "domains"

    MAX_DOMAIN_TITLE_LENGTH = 64

    DOMAIN_PAGE_SIZE_MIN = 1
    DOMAIN_PAGE_SIZE_DEFAULT = 10
    DOMAIN_PAGE_SIZE_MAX = 100

    MAX_DOMAINS_PER_USER = 100
    DEFAULT_LIMIT_PER_DOMAIN = 3

    CHECK_INTERVAL_SECONDS = 300  # 5 minutes

    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 0.5
    RETRY_MAX_DELAY = 5.0
    CONNECT_TIMEOUT = 5.0
    READ_TIMEOUT = 10.0

    PROBE_WORKERS = 30
    WRITER_WORKERS = 3
    PROBE_QUEUE_SIZE = 300
    WRITE_QUEUE_SIZE = 300

    SCHEDULER_ID = "domain_check_cycle"
    SCHEDULER_NAME = "Domain check cycle"
    SCHEDULER_MISFIRE_GRACE_SECONDS = 30
    SCHEDULER_MAX_INSTANCES = 1  # skip tick if previous cycle hasn't finished
    SCHEDULER_COALESCE = True  # merge missed ticks into one

    USER_AGENT_HEADER = "DomainMonitor/1.0 (+health-check)"
