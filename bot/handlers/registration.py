from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart

from bot.db.database import async_session
from bot.db.crud import get_user_by_telegram_id, create_user
from bot.keyboards.keyboards import main_menu, cancel_kb, skip_or_cancel_kb

router = Router()

SKIP = "⏭️ Пропустить"
CANCEL = "❌ Отмена"


class RegistrationForm(StatesGroup):
    waiting_name = State()
    waiting_group = State()
    waiting_artists = State()
    waiting_about = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

    if user and user.is_registered:
        await message.answer(
            f"С возвращением, *{user.name}*! 🎵\n\nВыбери действие:",
            reply_markup=main_menu,
            parse_mode="Markdown",
        )
        return

    await message.answer(
        "👋 Привет! Я помогаю находить людей со схожими музыкальными вкусами.\n\n"
        "Давай заполним анкету — это займёт минуту!\n\n"
        "Как тебя зовут?",
        reply_markup=cancel_kb,
        parse_mode="Markdown",
    )
    await state.set_state(RegistrationForm.waiting_name)


@router.message(RegistrationForm.waiting_name)
async def process_name(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await state.clear()
        await message.answer("Отменено. Напиши /start чтобы начать заново.")
        return

    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов. Попробуй снова:")
        return

    await state.update_data(name=name)
    await message.answer(
        f"Отлично, *{name}*! 🎉\n\nИз какой ты учебной группы?",
        reply_markup=skip_or_cancel_kb,
        parse_mode="Markdown",
    )
    await state.set_state(RegistrationForm.waiting_group)


@router.message(RegistrationForm.waiting_group)
async def process_group(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await state.clear()
        await message.answer("Отменено. Напиши /start чтобы начать заново.")
        return

    group = None if message.text == SKIP else message.text.strip()
    await state.update_data(group=group)
    await message.answer(
        "🎵 Напиши своих *3–5 любимых исполнителей* через запятую.\n\n"
        "Именно по ним тебя будут находить другие!\n\n"
        "Пример: темный принц, OG Buda, Eminem",
        reply_markup=cancel_kb,
        parse_mode="Markdown",
    )
    await state.set_state(RegistrationForm.waiting_artists)


@router.message(RegistrationForm.waiting_artists)
async def process_artists(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await state.clear()
        await message.answer("Отменено. Напиши /start чтобы начать заново.")
        return

    artists_list = [a.strip().title() for a in message.text.split(",") if a.strip()]
    if len(artists_list) < 1:
        await message.answer("Укажи хотя бы одного исполнителя через запятую:")
        return
    if len(artists_list) > 10:
        await message.answer("Слишком много! Укажи не более 10 исполнителей:")
        return

    await state.update_data(artists=", ".join(artists_list))
    await message.answer(
        "📝 Расскажи немного *о себе*: чем занимаешься, что ищешь в общении?",
        reply_markup=skip_or_cancel_kb,
        parse_mode="Markdown",
    )
    await state.set_state(RegistrationForm.waiting_about)


@router.message(RegistrationForm.waiting_about)
async def process_about(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await state.clear()
        await message.answer("Отменено. Напиши /start чтобы начать заново.")
        return

    about = None if message.text == SKIP else message.text.strip()
    data = await state.get_data()

    async with async_session() as session:
        user = await create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            name=data["name"],
            group_name=data.get("group"),
            artists=data["artists"],
            about=about,
        )

    await state.clear()
    await message.answer(
        f"✅ *Анкета создана!*\n\n{user.display_profile(show_contacts=True)}\n\n"
        "Теперь ищи людей со схожими вкусами 🎶",
        reply_markup=main_menu,
        parse_mode="Markdown",
    )
