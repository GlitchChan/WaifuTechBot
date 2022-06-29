import logging

from rich.logging import RichHandler

from secrets import DEBUG

__all__ = ("get_logger",)


def get_logger(
        name: str, show_locals: bool = True, format: str = "%x %H:%M:%S.%f"
) -> logging.Logger:
    """
    Get a pre-configured logger

    :param name: Name of the logger
    :returns: A Logger
    """
    __logger = logging.getLogger(name)
    __handler = RichHandler(
        rich_tracebacks=True, tracebacks_show_locals=show_locals, log_time_format=f"[{format}]"
    )
    __logger.addHandler(__handler)
    __logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    return __logger
