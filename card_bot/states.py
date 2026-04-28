from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    name = State()
    age = State()


class TemplateCreation(StatesGroup):
    name = State()
    card_type = State()
    organization = State()
    full_name = State()
    position = State()
    phone = State()
    email = State()
    website = State()
    address = State()
    slogan = State()
    colors = State()
    expiry = State()
    notes = State()
    confirm = State()


class TemplateUse(StatesGroup):
    choose = State()
    confirm = State()
