class AuthConfig:
    api_prefix = "/auth"
    api_tag = "auth"

    backend_name = "session_auth"

    cookie_name: str = "session_auth_cookie"
    cookie_max_age = 3600

    session_ttl = 3600
