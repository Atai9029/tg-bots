from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router(name='start')


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    logger.info('User %d (%s) /start', user.id, user.username or 'no-username')

    if message.chat.type != 'private':
        logger.warning('Bot used in non-private chat: chat_id=%d type=%s', message.chat.id, message.chat.type)

    await message.answer(
        '🎵 <b>Music Bot</b>\n\n'
        f'Hi {user.first_name}! I can search YouTube and send you songs as MP3 files.\n\n'
        '<b>How to use:</b>\n'
        '  1. Type any song name or artist\n'
        '  2. Pick a track from the list\n'
        '  3. Receive the MP3 directly in this chat\n\n'
        '<b>Commands:</b>\n'
        '  /start — Show this message\n'
        '  /help  — Detailed help\n\n'
        '🔍 <i>Just type a song name to get started…</i>'
    )


@router.message(Command('help'))
async def cmd_help(message: Message) -> None:
    logger.info('User %d requested /help', message.from_user.id)

    await message.answer(
        '🎵 <b>Music Bot — Help</b>\n\n'
        '📌 <b>Searching</b>\n'
        'Type any song title, artist name, or both:\n'
        '<code>Billie Eilish Bad Guy</code>\n'
        '<code>Bohemian Rhapsody Queen</code>\n\n'
        '📌 <b>Downloading</b>\n'
        'Tap any track in the result list to download it as an MP3.\n\n'
        '📌 <b>Limits</b>\n'
        '• Up to 5 results are shown per search\n'
        '• Maximum file size: 50 MB\n'
        '• Search results expire after 5 minutes\n\n'
        '📌 <b>Powered by</b>\n'
        'YouTube (via yt-dlp) + FFmpeg\n\n'
        '⚠️ <i>Please respect copyright law and only download music you are entitled to use.</i>'
    )
