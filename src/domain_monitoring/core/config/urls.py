class AppUrlSettings:
    ENTRY_LOGIN_PAGE = "/login"
    ENTRY_REGISTER_PAGE = "/register"

    USER_ROOT_DASHBOARD_PAGE = "/dashboard"

    def __init__(self, app_base_url: str):
        self.APP_BASE = app_base_url
