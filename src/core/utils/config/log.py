class LoggingSettings:
    level: str = "DEBUG"
    lib_level: str = "WARNING"
    time_format: str = "%Y-%m-%d %H:%M:%S"
    formatter: str = "%(name)s - [ %(funcName)s() ] - %(message)s"
