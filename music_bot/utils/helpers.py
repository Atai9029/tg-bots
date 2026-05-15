from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)


def sanitize_filename(name: str, max_length: int = 80) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    sanitized = sanitized.strip('. ')
    return sanitized[:max_length] or 'track'


def format_duration(seconds: int | None) -> str:
    if not seconds:
        return '?:??'
    seconds = int(seconds)
    minutes, secs = divmod(seconds, 60)
    return f'{minutes}:{secs:02d}'


def format_file_size(byte_count: int) -> str:
    value = float(byte_count)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if value < 1024 or unit == 'TB':
            return f'{value:.1f} {unit}'
        value /= 1024
    return f'{value:.1f} TB'


def truncate(text: str, max_length: int, ellipsis: str = '…') -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - len(ellipsis)] + ellipsis


def cleanup_file(filepath: str | os.PathLike) -> None:
    try:
        path = str(filepath)
        if os.path.exists(path):
            os.remove(path)
            logger.debug('Removed temp file: %s', path)
    except OSError as exc:
        logger.warning('Could not remove temp file %s: %s', filepath, exc)
