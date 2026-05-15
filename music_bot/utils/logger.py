from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

from config.settings import settings

_COLOURS = {
    logging.DEBUG: '\033[36m',
    logging.INFO: '\033[32m',
    logging.WARNING: '\033[33m',
    logging.ERROR: '\033[31m',
    logging.CRITICAL: '\033[35m',
}
_RESET = '\033[0m'


class _ColourFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelno, '')
        record.levelname = f'{colour}{record.levelname:<8}{_RESET}'
        return super().format(record)


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(getattr(logging, settings.LOG_LEVEL))

    fmt_str = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    date_fmt = '%Y-%m-%d %H:%M:%S'

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_ColourFormatter(fmt=fmt_str, datefmt=date_fmt))
    root.addHandler(console_handler)

    log_path: Path = settings.LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setFormatter(logging.Formatter(fmt=fmt_str, datefmt=date_fmt))
    root.addHandler(file_handler)

    for noisy in ('httpx', 'httpcore', 'aiohttp', 'asyncio'):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        'Logging initialised level=%s file=%s', settings.LOG_LEVEL, log_path
    )
