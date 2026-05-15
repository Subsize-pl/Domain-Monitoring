import ipaddress
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlsplit

from domain_monitoring.core.exceptions.domain_validation import (
    DomainValidationException,
)

# RFC-compliant domain label validation:
# - 1..63 chars
# - letters, digits, hyphens
# - cannot start/end with hyphen
_DOMAIN_LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")

# RFC Maximum Full Domain Length
MAXIMUM_DOMAIN_LENGTH = 253


@dataclass(frozen=True, slots=True)
class DomainNormalizationResult:
    original: str
    normalized: str


def normalize_and_validate_domain(raw_value: str) -> DomainNormalizationResult:
    """
    Normalize and validate a domain name.

    Supported input:
        - google.com
        - https://google.com
        - пример.рф

    Rejected input:
        - localhost
        - IP addresses
        - URLs with paths/query params/fragments
        - credentials
        - ports

    Returns canonical ASCII host suitable for DB storage.
    """

    if raw_value is None:
        raise DomainValidationException("Domain value is required.")

    value = unicodedata.normalize("NFKC", raw_value).strip().lower()

    if not value:
        raise DomainValidationException("Domain value cannot be empty.")

    if any(ch.isspace() for ch in value):
        raise DomainValidationException(
            "Domain value must not contain spaces.",
        )

    # urlsplit works more reliably when a scheme exists
    if "://" not in value:
        value = f"http://{value}"

    parsed = urlsplit(value)

    # Explicitly reject credentials in URLs
    if parsed.username is not None or parsed.password is not None:
        raise DomainValidationException(
            "Credentials are not allowed in domain value.",
        )

    try:
        port = parsed.port
    except ValueError as exc:
        raise DomainValidationException(
            "Port is invalid. Provide only a domain name.",
        ) from exc

    # This service stores domains only, not host:port pairs
    if port is not None:
        raise DomainValidationException(
            "Port is not allowed. Provide only a domain name."
        )

    # Query parameters and fragments are not meaningful for domain monitoring
    if parsed.query or parsed.fragment:
        raise DomainValidationException(
            "Query parameters and fragments are not allowed."
        )

    # Reject paths like:
    #   - google.com/test
    # but allow:
    #   - google.com
    #   - google.com/
    if parsed.path not in ("", "/"):
        raise DomainValidationException(
            "Path is not allowed. Provide only a domain name.",
        )

    host = parsed.hostname

    if not host:
        raise DomainValidationException("Invalid domain.")

    # Remove trailing DNS dot:
    #   google.com. -> google.com
    host = host.rstrip(".")

    if host == "localhost" or host.endswith(".localhost"):
        raise DomainValidationException("localhost is not allowed.")

    # Reject IPv4/IPv6 addresses
    try:
        ipaddress.ip_address(host)
        raise DomainValidationException(
            "IP addresses are not allowed. Provide a domain name."
        )
    except ValueError:
        pass

    # Convert international domains to punycode ASCII representation
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise DomainValidationException(
            "Invalid international domain name.",
        ) from exc

    if len(ascii_host) > MAXIMUM_DOMAIN_LENGTH:
        raise DomainValidationException("Domain name is too long.")

    labels = ascii_host.split(".")

    # Require at least one dot:
    #   google.com -> valid
    #   google -> invalid
    if len(labels) < 2:
        raise DomainValidationException("Domain must contain at least one dot.")

    # Validate every domain label independently
    for label in labels:
        if not label:
            raise DomainValidationException("Domain contains an empty label.")

        if not _DOMAIN_LABEL_RE.fullmatch(label):
            raise DomainValidationException(f"Invalid domain label: {label}")

    # Basic TLD (Top-Level Domain) sanity check
    # tld = labels[-1]
    #
    # _DOMAIN_TLD_RE = re.compile(r"^(xn--)?[a-z0-9-]{2,63}$")
    # if not _DOMAIN_TLD_RE.fullmatch(tld):
    #     raise DomainValidationException("Top-level domain looks invalid.")

    return DomainNormalizationResult(
        original=raw_value,
        normalized=ascii_host,
    )
