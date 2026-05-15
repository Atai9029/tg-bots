from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from keyboards.inline import build_track_list_keyboard
from services.music_search import search_music
from utils.helpers import format_duration, truncate
from utils.search_cache import cache

logger = logging.getLogger(__name__)
router = Router(name='search')

_MIN_QUERY_LEN = 2
_MAX_QUERY_LEN = 100


def _format_results_text(query: str, tracks: list[dict]) -> str:
    lines = [f'🎵 <b>Results for:</b> <i>{query}</i>\n']
    for i, track in enumerate(tracks, start=1):
        title = truncate(track.get('title', 'Unknown'), 55)
        uploader = truncate(track.get('uploader', 'Unknown'), 30)
        duration = format_duration(track.get('duration'))
        lines.append(f'{i}. <b>{title}</b>\n   👤 {uploader}  ⏱ {duration}\n')
    lines.append('👇 <i>Tap a track to download it as MP3:</i>')
    return '\n'.join(lines)


@router.message(F.text & ~F.text.startswith('/'))
async def handle_search(message: Message) -> None:
    query = (message.text or '').strip()
    user_id = message.from_user.id

    if len(query) < _MIN_QUERY_LEN:
        await message.answer(f'⚠️ Please enter at least {_MIN_QUERY_LEN} characters.')
        return

    if len(query) > _MAX_QUERY_LEN:
        await message.answer(f'⚠️ Query is too long (max {_MAX_QUERY_LEN} characters).')
        return

    logger.info('User %d searching: %r', user_id, query)

    status_msg = await message.answer(
        f'🔍 <i>Searching for</i> <b>{query}</b>\n'
        '<i>This usually takes a few seconds…</i>'
    )

    try:
        tracks = await search_music(query)
    except Exception as exc:  # noqa: BLE001
        logger.error('search_music raised unexpectedly: %s', exc, exc_info=True)
        await status_msg.edit_text(
            '❌ <b>Something went wrong while searching.</b>\n'
            'Please try again in a moment.'
        )
        return

    if not tracks:
        await status_msg.edit_text(
            '🔍 <b>No results found.</b>\n\n'
            'Try a different spelling or a more specific title.'
        )
        return

    cache.set(user_id, tracks)
    keyboard = build_track_list_keyboard(tracks, user_id)

    await status_msg.edit_text(_format_results_text(query, tracks), reply_markup=keyboard)
