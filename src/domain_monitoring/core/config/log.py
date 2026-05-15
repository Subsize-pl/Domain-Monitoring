class LoggingSettings:
    level: str
    time_format: str
    formatter: str = "%(name)s - [ %(funcName)s() ] - %(message)s"

    def __init__(
        self,
        level: str = "DEBUG",
        time_format: str = "%Y-%m-%d %H:%M:%S",
    ):
        self.level = level
        self.time_format = time_format
