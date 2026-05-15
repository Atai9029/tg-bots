from __future__ import annotations

import logging
from typing import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.helpers import format_duration, truncate

logger = logging.getLogger(__name__)


class TrackCallbackData(CallbackData, prefix='track'):
    index: int
    user_id: int


class CancelCallbackData(CallbackData, prefix='cancel'):
    user_id: int


def build_track_list_keyboard(tracks: Sequence[dict], user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for index, track in enumerate(tracks):
        duration = format_duration(track.get('duration'))
        label = truncate(track.get('title', 'Unknown'), max_length=35)
        button_text = f'🎵 {index + 1}. {label}  [{duration}]'
        builder.button(
            text=button_text,
            callback_data=TrackCallbackData(index=index, user_id=user_id),
        )

    builder.button(text='❌  Cancel', callback_data=CancelCallbackData(user_id=user_id))
    builder.adjust(1)
    return builder.as_markup()


def build_download_again_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='🔍  New search', callback_data=CancelCallbackData(user_id=user_id))
    builder.adjust(1)
    return builder.as_markup()
