from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.database import async_session
from bot.db.crud import get_user_by_telegram_id, update_user
from bot.keyboards.keyboards import (
    main_menu,
    cancel_kb,
    skip_or_cancel_kb,
    delete_or_cancel_kb,
    edit_profile_kb,
)

router = Router()

CANCEL = "❌ Отмена"
SKIP = "⏭️ Пропустить"
DELETE = "🗑️ Удалить"


class EditProfileForm(StatesGroup):
    waiting_new_artists = State()
    waiting_new_about = State()
    waiting_new_group = State()


@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

    if not user or not user.is_registered:
        await message.answer("Сначала зарегистрируйся! /start")
        return

    await message.answer(
        f"👤 *Твой профиль:*\n\n{user.display_profile(show_contacts=True)}",
        reply_markup=edit_profile_kb,
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "edit:artists")
async def edit_artists(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✏️ Введи новый список исполнителей через запятую:",
        reply_markup=cancel_kb,
    )
    await state.set_state(EditProfileForm.waiting_new_artists)
    await callback.answer()


@router.message(EditProfileForm.waiting_new_artists)
async def save_new_artists(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu)
        return

    artists_list = [a.strip() for a in message.text.split(",") if a.strip()]
    if not artists_list:
        await message.answer("Укажи хотя бы одного исполнителя:")
        return

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        await update_user(session, user, artists=", ".join(artists_list))

    await state.clear()
    await message.answer("✅ Исполнители обновлены!", reply_markup=main_menu)


@router.callback_query(F.data == "edit:about")
async def edit_about(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✏️ Расскажи о себе:",
        reply_markup=delete_or_cancel_kb,
    )
    await state.set_state(EditProfileForm.waiting_new_about)
    await callback.answer()


@router.message(EditProfileForm.waiting_new_about)
async def save_new_about(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu)
        return

    about = None if message.text == DELETE else message.text.strip()

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        await update_user(session, user, about=about)

    await state.clear()
    await message.answer("✅ Информация о себе обновлена!", reply_markup=main_menu)


@router.callback_query(F.data == "edit:group")
async def edit_group(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✏️ Введи название группы:",
        reply_markup=delete_or_cancel_kb,
    )
    await state.set_state(EditProfileForm.waiting_new_group)
    await callback.answer()


@router.message(EditProfileForm.waiting_new_group)
async def save_new_group(message: Message, state: FSMContext):
    if message.text == CANCEL:
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu)
        return

    group = None if message.text == DELETE else message.text.strip()

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        await update_user(session, user, group_name=group)

    await state.clear()
    await message.answer("✅ Группа обновлена!", reply_markup=main_menu)
