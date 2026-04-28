from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from db import db
from keyboards import cancel_kb, yes_no_kb, finish_template_kb, template_selection_kb, TemplateCb
from states import TemplateCreation, TemplateUse
from services.gemini import polish_card_text
from services.card_renderer import render_card

router = Router()

FIELDS = [
    ("name", "Как назвать этот шаблон?"),
    ("card_type", "Что это будет: визитка, пропуск, членская карта или другое?"),
    ("organization", "Как называется ваша организация?"),
    ("full_name", "Введите ФИО или имя владельца карточки."),
    ("position", "Какая должность, роль или статус?"),
    ("phone", "Введите телефон."),
    ("email", "Введите email."),
    ("website", "Введите сайт или Telegram/Instagram, если нужно."),
    ("address", "Введите адрес или город."),
    ("slogan", "Введите слоган или короткую подпись."),
    ("colors", "Введите цвет шаблона: dark, light, blue, green, red или gold."),
    ("expiry", "Введите срок действия или дату окончания."),
    ("notes", "Введите дополнительные данные или оставьте любой текст."),
]


async def _ask_next(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    step = data.get("step", 0)
    if step >= len(FIELDS):
        await state.set_state(TemplateCreation.confirm)
        summary = await state.get_data()
        text = (
            f"Проверьте шаблон:\n\n"
            f"Название: {summary.get('name', '')}\n"
            f"Тип: {summary.get('card_type', '')}\n"
            f"Организация: {summary.get('organization', '')}\n"
            f"Владелец: {summary.get('full_name', '')}\n"
            f"Роль: {summary.get('position', '')}\n"
            f"Телефон: {summary.get('phone', '')}\n"
            f"Email: {summary.get('email', '')}\n"
            f"Сайт: {summary.get('website', '')}\n"
            f"Адрес: {summary.get('address', '')}\n"
            f"Слоган: {summary.get('slogan', '')}\n"
            f"Цвет: {summary.get('colors', '')}\n"
            f"Срок: {summary.get('expiry', '')}\n"
            f"Примечания: {summary.get('notes', '')}\n"
        )
        await message.answer(text, reply_markup=finish_template_kb())
        return

    _, question = FIELDS[step]
    await state.set_state(getattr(TemplateCreation, FIELDS[step][0]))
    await message.answer(question, reply_markup=cancel_kb())


@router.callback_query(F.data == "gen:create")
async def create_template_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.update_data(step=0)
    await callback.message.answer("Начинаем создание шаблона.")
    await _ask_next(callback.message, state)


@router.message(TemplateCreation.name)
async def step_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip(), step=1)
    await _ask_next(message, state)


@router.message(TemplateCreation.card_type)
async def step_card_type(message: Message, state: FSMContext):
    await state.update_data(card_type=message.text.strip(), step=2)
    await _ask_next(message, state)


@router.message(TemplateCreation.organization)
async def step_org(message: Message, state: FSMContext):
    await state.update_data(organization=message.text.strip(), step=3)
    await _ask_next(message, state)


@router.message(TemplateCreation.full_name)
async def step_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip(), step=4)
    await _ask_next(message, state)


@router.message(TemplateCreation.position)
async def step_position(message: Message, state: FSMContext):
    await state.update_data(position=message.text.strip(), step=5)
    await _ask_next(message, state)


@router.message(TemplateCreation.phone)
async def step_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip(), step=6)
    await _ask_next(message, state)


@router.message(TemplateCreation.email)
async def step_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip(), step=7)
    await _ask_next(message, state)


@router.message(TemplateCreation.website)
async def step_website(message: Message, state: FSMContext):
    await state.update_data(website=message.text.strip(), step=8)
    await _ask_next(message, state)


@router.message(TemplateCreation.address)
async def step_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip(), step=9)
    await _ask_next(message, state)


@router.message(TemplateCreation.slogan)
async def step_slogan(message: Message, state: FSMContext):
    await state.update_data(slogan=message.text.strip(), step=10)
    await _ask_next(message, state)


@router.message(TemplateCreation.colors)
async def step_colors(message: Message, state: FSMContext):
    await state.update_data(colors=message.text.strip(), step=11)
    await _ask_next(message, state)


@router.message(TemplateCreation.expiry)
async def step_expiry(message: Message, state: FSMContext):
    await state.update_data(expiry=message.text.strip(), step=12)
    await _ask_next(message, state)


@router.message(TemplateCreation.notes)
async def step_notes(message: Message, state: FSMContext):
    await state.update_data(notes=message.text.strip(), step=13)
    await _ask_next(message, state)


@router.callback_query(F.data == "tpl:finish")
async def finish_template(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.answer("Сначала пройдите /start.")
        return
    template_data = {k: data.get(k, "") for k, _ in FIELDS}
    template_id = await db.create_template(user["id"], template_data)
    await state.update_data(saved_template_id=template_id)
    await callback.message.answer(
        f"Шаблон сохранён. Применить его сейчас?\nШаблон №{template_id}",
        reply_markup=yes_no_kb("tpl:apply_yes", "tpl:apply_no"),
    )


@router.callback_query(F.data == "tpl:apply_yes")
async def apply_saved_template(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    template_id = data.get("saved_template_id")
    if not template_id:
        await callback.message.answer("Шаблон не найден.")
        return
    await callback.message.answer("Ожидайте, я генерирую карточку...")
    template = await db.get_template(int(template_id))
    polished = await polish_card_text(dict(template))
    output_path = f"generated/card_{template_id}_{callback.from_user.id}.png"
    render_card(dict(template), polished, output_path)
    await db.save_generated_card(int(template["user_id"]), int(template_id), output_path, str(polished))
    await callback.message.answer_photo(FSInputFile(output_path), caption="Карточка готова.")
    await state.clear()


@router.callback_query(F.data == "tpl:apply_no")
async def apply_saved_template_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Шаблон сохранён без генерации.")
    await state.clear()


@router.callback_query(F.data == "gen:use")
async def use_template_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.answer("Сначала пройдите /start.")
        return
    templates = await db.get_templates(user["id"])
    if not templates:
        await callback.message.answer("У вас ещё нет шаблонов. Сначала создайте шаблон.")
        return
    items = [(int(t["id"]), f"{t['name']} — {t['organization']}") for t in templates]
    await state.set_state(TemplateUse.choose)
    await callback.message.answer("Выберите шаблон:", reply_markup=template_selection_kb(items))


@router.callback_query(TemplateCb.filter(F.action == "pick"))
async def pick_template(callback: CallbackQuery, callback_data: TemplateCb, state: FSMContext):
    await callback.answer()
    template = await db.get_template(int(callback_data.template_id))
    if not template:
        await callback.message.answer("Шаблон не найден.")
        return
    await state.update_data(chosen_template_id=int(template["id"]))
    await callback.message.answer(
        f"Использовать шаблон «{template['name']}»?",
        reply_markup=yes_no_kb("tpl:use_yes", "tpl:use_no"),
    )


@router.callback_query(F.data == "tpl:use_yes")
async def use_template_yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    template_id = data.get("chosen_template_id")
    if not template_id:
        await callback.message.answer("Шаблон не выбран.")
        return
    template = await db.get_template(int(template_id))
    await callback.message.answer("Ожидайте, я генерирую карточку...")
    polished = await polish_card_text(dict(template))
    output_path = f"generated/card_{template_id}_{callback.from_user.id}.png"
    render_card(dict(template), polished, output_path)
    await db.save_generated_card(int(template["user_id"]), int(template_id), output_path, str(polished))
    await callback.message.answer_photo(FSInputFile(output_path), caption="Карточка готова.")
    await state.clear()


@router.callback_query(F.data == "tpl:use_no")
async def use_template_no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Генерация отменена.")
    await state.clear()
