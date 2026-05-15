from __future__ import annotations

import logging

from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile

from keyboards.inline import CancelCallbackData, TrackCallbackData
from services.music_downloader import download_music
from utils.helpers import cleanup_file, format_duration, sanitize_filename, truncate
from utils.search_cache import cache

logger = logging.getLogger(__name__)
router = Router(name='download')


async def _safe_delete_message(callback: CallbackQuery) -> None:
    try:
        await callback.message.delete()
    except (TelegramBadRequest, Exception) as exc:
        logger.debug('Could not delete keyboard message: %s', exc)


@router.callback_query(TrackCallbackData.filter())
async def handle_track_download(callback: CallbackQuery, callback_data: TrackCallbackData) -> None:
    caller_id = callback.from_user.id
    owner_id = callback_data.user_id
    track_idx = callback_data.index

    if caller_id != owner_id:
        await callback.answer('⛔ These buttons belong to someone else\'s search.', show_alert=True)
        return

    tracks = cache.get(owner_id)
    if tracks is None:
        await callback.answer('⏰ Search results have expired. Please search again.', show_alert=True)
        try:
            await callback.message.edit_text(
                '⏰ <b>Results expired.</b>\nSend a new search query to start over.',
                reply_markup=None,
            )
        except TelegramBadRequest:
            pass
        return

    if track_idx < 0 or track_idx >= len(tracks):
        await callback.answer('❌ Invalid track index.', show_alert=True)
        return

    track = tracks[track_idx]
    logger.info('User %d requested download: [%d] %r', caller_id, track_idx, track.get('title'))

    await callback.answer('⬇️ Download started…')

    try:
        await callback.message.edit_text(
            f'⬇️ <b>Downloading…</b>\n\n'
            f'🎵 <b>{truncate(track["title"], 60)}</b>\n'
            f'👤 {truncate(track["uploader"], 40)}\n'
            f'⏱ {format_duration(track.get("duration"))}\n\n'
            '<i>Please wait — this can take up to a minute for longer tracks.</i>',
            reply_markup=None,
        )
    except TelegramBadRequest as exc:
        logger.warning('Could not edit progress message: %s', exc)

    filepath: str | None = None
    try:
        filepath = await download_music(track['url'], track['id'])

        if filepath is None:
            await callback.message.edit_text(
                '❌ <b>Download failed.</b>\n\n'
                'Possible reasons:\n'
                '• The video is geo-restricted or age-gated\n'
                '• The file would exceed the 50 MB limit\n'
                '• Temporary YouTube issue\n\n'
                'Please try a different track.',
            )
            return

        audio_file = FSInputFile(
            path=filepath,
            filename=f"{sanitize_filename(track['title'])}.mp3",
        )

        await callback.message.answer_audio(
            audio=audio_file,
            title=track['title'],
            performer=track['uploader'],
            duration=track.get('duration') or None,
            caption=(
                f'🎵 <b>{truncate(track["title"], 60)}</b>\n'
                f'👤 {track["uploader"]}\n\n'
                '<i>Delivered by Music Bot 🎧</i>'
            ),
        )

        logger.info('Sent audio to user %d: %r', caller_id, track.get('title'))
        await _safe_delete_message(callback)

    except Exception as exc:  # noqa: BLE001
        logger.error('Download handler error for user %d: %s', caller_id, exc, exc_info=True)
        try:
            await callback.message.edit_text(
                '❌ <b>An unexpected error occurred.</b>\n'
                'Please try again or choose a different track.',
            )
        except TelegramBadRequest:
            pass
    finally:
        if filepath:
            cleanup_file(filepath)


@router.callback_query(CancelCallbackData.filter())
async def handle_cancel(callback: CallbackQuery, callback_data: CancelCallbackData) -> None:
    if callback.from_user.id != callback_data.user_id:
        await callback.answer('⛔ These buttons belong to someone else\'s search.', show_alert=True)
        return

    cache.clear(callback_data.user_id)
    await callback.answer('✅ Cancelled')

    try:
        await callback.message.edit_text(
            '🔍 <b>Search cancelled.</b>\nType a song name whenever you\'re ready.',
            reply_markup=None,
        )
    except TelegramBadRequest:
        pass

    logger.info('User %d cancelled search.', callback.from_user.id)
