class LoggingSettings:
    level: str
    lib_level: str
    time_format: str
    formatter: str = "%(name)s - [ %(funcName)s() ] - %(message)s"

    def __init__(
        self,
        level: str = "DEBUG",
        lib_level: str = "WARNING",
        time_format: str = "%Y-%m-%d %H:%M:%S",
    ):
        self.level = level
        self.lib_level = lib_level
        self.time_format = time_format
