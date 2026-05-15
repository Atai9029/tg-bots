from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from config.settings import settings

logger = logging.getLogger(__name__)
_search_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='search')


def _build_track(entry: dict) -> dict:
    video_id = entry.get('id', '')
    return {
        'id': video_id,
        'title': entry.get('title') or 'Unknown Title',
        'uploader': entry.get('uploader') or entry.get('channel') or entry.get('artist') or 'Unknown Artist',
        'duration': int(entry.get('duration') or 0),
        'url': f'https://www.youtube.com/watch?v={video_id}',
        'thumbnail': entry.get('thumbnail') or '',
    }


def _search_sync(query: str, max_results: int) -> list[dict]:
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
    }

    search_query = f'ytsearch{max_results}:{query}'
    logger.debug('yt-dlp search query: %r', search_query)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            raw = ydl.extract_info(search_query, download=False)

        if not raw or 'entries' not in raw:
            logger.warning('yt-dlp returned no entries for query %r', query)
            return []

        tracks: list[dict] = []
        for entry in raw['entries']:
            if entry and entry.get('id'):
                tracks.append(_build_track(entry))

        logger.info("Search '%s' -> %d results", query, len(tracks))
        return tracks
    except yt_dlp.utils.DownloadError as exc:
        logger.error('yt-dlp DownloadError during search: %s', exc)
        return []
    except Exception as exc:  # noqa: BLE001
        logger.error('Unexpected search error: %s', exc, exc_info=True)
        return []


async def search_music(query: str) -> list[dict]:
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(_search_executor, _search_sync, query, settings.MAX_SEARCH_RESULTS)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error('search_music wrapper error: %s', exc, exc_info=True)
        return []
