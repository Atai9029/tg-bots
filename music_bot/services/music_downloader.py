from __future__ import annotations

import asyncio
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yt_dlp

from config.settings import settings

logger = logging.getLogger(__name__)
_download_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='download')


def _download_sync(video_url: str, video_id: str) -> str | None:
    dl_path = Path(settings.DOWNLOAD_PATH)
    dl_path.mkdir(parents=True, exist_ok=True)

    unique_stem = f'{video_id}_{uuid.uuid4().hex[:8]}'
    output_template = str(dl_path / f'{unique_stem}.%(ext)s')
    expected_mp3 = str(dl_path / f'{unique_stem}.mp3')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
    }

    logger.info('Starting download: %s (id=%s)', video_url, video_id)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except yt_dlp.utils.DownloadError as exc:
        logger.error('yt-dlp DownloadError: %s', exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error('Unexpected download error: %s', exc, exc_info=True)
        return None

    if not os.path.exists(expected_mp3):
        logger.error('Expected MP3 not found after download: %s', expected_mp3)
        return None

    size_bytes = os.path.getsize(expected_mp3)
    size_mb = size_bytes / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        logger.warning('File too large (%.1f MB > %d MB): %s', size_mb, settings.MAX_FILE_SIZE_MB, expected_mp3)
        os.remove(expected_mp3)
        return None

    logger.info('Download complete: %s (%.1f MB)', expected_mp3, size_mb)
    return expected_mp3


async def download_music(video_url: str, video_id: str) -> str | None:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(_download_executor, _download_sync, video_url, video_id)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error('download_music wrapper error: %s', exc, exc_info=True)
        return None
