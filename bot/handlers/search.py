from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.db.database import async_session
from bot.db.crud import (
    get_user_by_telegram_id,
    search_users_by_artist,
    create_connect_request,
    get_connect_request,
)
from bot.keyboards.keyboards import main_menu, cancel_kb, profile_actions_kb

router = Router()

RESULTS_KEY = "search_results"
INDEX_KEY = "search_index"


class SearchForm(StatesGroup):
    waiting_artist = State()


@router.message(F.text == "🔍 Найти по исполнителю")
async def start_search(message: Message, state: FSMContext):
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

    if not user or not user.is_registered:
        await message.answer("Сначала зарегистрируйся! Напиши /start")
        return

    await message.answer(
        "🔍 Введи имя исполнителя для поиска:\n\nНапример: _Playboi Carti_",
        reply_markup=cancel_kb,
        parse_mode="Markdown",
    )
    await state.set_state(SearchForm.waiting_artist)


@router.message(SearchForm.waiting_artist)
async def process_search(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Поиск отменён.", reply_markup=main_menu)
        return

    artist = message.text.strip()
    if len(artist) < 2:
        await message.answer("Слишком короткий запрос, попробуй снова:")
        return

    async with async_session() as session:
        results = await search_users_by_artist(session, artist, message.from_user.id)

    if not results:
        await message.answer(
            f"😕 По запросу *{artist}* никого не нашлось.\n\nВведи другого исполнителя или нажми ❌ Отмена:",
            parse_mode="Markdown",
        )
        return

    await state.set_state(None)
    await state.update_data(
        **{
            RESULTS_KEY: [u.telegram_id for u in results],
            INDEX_KEY: 0,
        }
    )

    await message.answer(
        f"🎵 Найдено *{len(results)}* чел. по запросу «{artist}»\n\n"
        f"*Анкета 1 из {len(results)}:*\n\n{results[0].display_profile()}",
        reply_markup=profile_actions_kb(results[0].telegram_id),
        parse_mode="Markdown",
    )
    await message.answer("Выбери действие:", reply_markup=main_menu)


@router.callback_query(F.data == "next_result")
async def next_result(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    results = data.get(RESULTS_KEY, [])
    index = data.get(INDEX_KEY, 0) + 1

    if index >= len(results):
        await callback.answer("Больше результатов нет!", show_alert=True)
        return

    await state.update_data(**{INDEX_KEY: index})
    target_tg_id = results[index]

    async with async_session() as session:
        target = await get_user_by_telegram_id(session, target_tg_id)

    if not target:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await callback.message.edit_text(
        f"*Анкета {index + 1} из {len(results)}:*\n\n{target.display_profile()}",
        reply_markup=profile_actions_kb(target.telegram_id),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("send_req:"))
async def send_connect_request(callback: CallbackQuery):
    target_tg_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        sender = await get_user_by_telegram_id(session, callback.from_user.id)
        receiver = await get_user_by_telegram_id(session, target_tg_id)

        if not sender or not receiver:
            await callback.answer("Ошибка. Попробуй снова.", show_alert=True)
            return

        existing = await get_connect_request(session, sender.id, receiver.id)
        if existing:
            await callback.answer(
                "Ты уже отправил запрос этому пользователю!", show_alert=True
            )
            return

        req = await create_connect_request(session, sender.id, receiver.id)

        sender_profile = sender.display_profile(show_contacts=False)
        receiver_tg_id = receiver.telegram_id
        req_id = req.id

    try:
        from aiogram import Bot
        from bot.config import BOT_TOKEN
        from bot.keyboards.keyboards import request_response_kb

        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=receiver_tg_id,
            text=f"💌 *Новый запрос на знакомство!*\n\n{sender_profile}\n\nХочет познакомиться с тобой 🎵",
            reply_markup=request_response_kb(req_id),
            parse_mode="Markdown",
        )
        await bot.session.close()
    except Exception:
        pass

    await callback.answer("✅ Запрос отправлен!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)
