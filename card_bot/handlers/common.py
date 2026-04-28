from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from db import db
from keyboards import main_menu_kb, generation_menu_kb, cancel_kb
from states import Registration

router = Router()


async def _show_main(message: Message, user_row) -> None:
    await message.answer(
        f"Привет, {user_row['first_name']}!\n"
        f"Возраст: {user_row['age']}\n\n"
        f"Выбери раздел:",
        reply_markup=main_menu_kb(),
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await state.set_state(Registration.name)
        await message.answer("Добро пожаловать в бота «Создание карточек». Как вас зовут?", reply_markup=cancel_kb())
        return
    await _show_main(message, user)


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user:
        await _show_main(message, user)
    else:
        await message.answer("Действие отменено. Нажмите /start, чтобы начать заново.")


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    await callback.answer("Отменено")
    if user:
        await callback.message.edit_text("Действие отменено.")
        await callback.message.answer("Главное меню:", reply_markup=main_menu_kb())
    else:
        await callback.message.answer("Действие отменено. Нажмите /start.")


@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(Registration.age)
    await message.answer("Введите ваш возраст:", reply_markup=cancel_kb())


@router.message(Registration.age)
async def reg_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Возраст должен быть числом. Попробуйте ещё раз.")
        return
    data = await state.get_data()
    user = await db.create_or_update_user(
        telegram_id=message.from_user.id,
        first_name=data["name"],
        age=int(message.text),
        username=message.from_user.username,
    )
    await state.clear()
    await _show_main(message, user)


@router.message(F.text == "Профиль")
async def profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала пройдите регистрацию через /start.")
        return
    stats = await db.get_stats(user["id"])
    await message.answer(
        f"Профиль\n\n"
        f"Имя: {user['first_name']}\n"
        f"Возраст: {user['age']}\n"
        f"Username: @{user['username'] or 'не указан'}\n"
        f"Шаблонов: {stats['templates']}\n"
        f"Сгенерировано карточек: {stats['cards']}"
    )


@router.message(F.text == "Помощь")
async def help_message(message: Message):
    await message.answer(
        "Бот создаёт шаблоны для визиток, пропусков и членских карт.\n"
        "Нажмите «Генерация карточек», затем выберите создание шаблона или использование готового шаблона.\n"
        "Отмена доступна почти на каждом шаге."
    )


@router.message(F.text == "Генерация карточек")
async def generation(message: Message):
    await message.answer("Выберите действие:", reply_markup=generation_menu_kb())
