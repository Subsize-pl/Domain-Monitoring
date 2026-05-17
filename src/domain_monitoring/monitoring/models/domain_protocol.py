from enum import Enum


class DomainProtocol(str, Enum):
    https = "https"
    http = "http"
