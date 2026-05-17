from enum import Enum


class TlsStatus(str, Enum):
    valid = "valid"
    invalid = "invalid"
    not_checked = "not_checked"
