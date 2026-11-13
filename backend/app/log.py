"""Application logger: the terminal and a rotating file share one logger."""

from logging import Filter, Formatter, LogRecord, Logger, StreamHandler, getLogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

import backend.app.config as app_config

LOGGER_NAME = "flyngo"
_PATH_ATTR = "_flyngo_log_path"
_MAX_BYTES = 1_048_576
_BACKUP_COUNT = 3


class _SingleLine(Filter):
    """Keep each event on one line. A reason can contain a newline."""

    def filter(self, record: LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = " ".join(record.msg.split())
        if isinstance(record.args, tuple):
            record.args = tuple(
                " ".join(arg.split()) if isinstance(arg, str) else arg for arg in record.args
            )
        return True


def get_logger() -> Logger:
    """Return the FlyNGo logger. Call configure_logging before emitting records."""
    return getLogger(LOGGER_NAME)


def configure_logging(log_path: str | Path | None = None) -> Logger:
    """Attach a terminal handler and a rotating file handler.

    A second call with the same path keeps the existing handlers. A different
    path replaces them, which tests use to point at a temporary file.
    """
    path = Path(log_path) if log_path is not None else Path(app_config.LOG_PATH)
    path = path.resolve()
    logger = get_logger()
    logger.setLevel("INFO")
    logger.propagate = False
    if not any(isinstance(item, _SingleLine) for item in logger.filters):
        logger.addFilter(_SingleLine())
    if getattr(logger, _PATH_ATTR, None) == path and logger.handlers:
        return logger

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    path.parent.mkdir(parents=True, exist_ok=True)
    formatter = Formatter(
        "%(asctime)s %(levelname)s flyngo %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    stream = StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    try:
        rotating = RotatingFileHandler(
            path,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
    except OSError:
        setattr(logger, _PATH_ATTR, path)
        logger.warning("log file unavailable at %s", path)
        return logger
    rotating.setFormatter(formatter)
    logger.addHandler(rotating)
    setattr(logger, _PATH_ATTR, path)
    return logger
