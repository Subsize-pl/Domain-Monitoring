import logging

from rich.console import Console
from rich.logging import RichHandler

from core.config.settings import get_settings

# from ._lib_log_filter import LibraryLogFilter

settings = get_settings()


def setup_logging():
    rich_console = Console(
        style="bold cyan",  # Style for the console output
        width=200,
        force_terminal=True,  # Force terminal colors, even if not supported
    )

    rich_handler = RichHandler(
        console=rich_console,
        rich_tracebacks=True,  # Show rich tracebacks for errors
        tracebacks_show_locals=True,  # Show local variables in tracebacks
        tracebacks_word_wrap=False,  # Disable word wrapping in tracebacks
        log_time_format=settings.logging.time_format,
    )

    # Add a custom filter to control which logs are shown
    # rich_handler.addFilter(LibraryLogFilter())
    rich_handler.setFormatter(logging.Formatter(settings.logging.formatter))

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.logging.level)
    root_logger.addHandler(rich_handler)


def get_logger(name: str):
    return logging.getLogger(name)
