from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.db.database import async_session
from bot.db.crud import (
    get_user_by_telegram_id,
    get_pending_requests_for_user,
    get_accepted_connects,
    update_request_status,
)
from bot.db.models import ConnectRequest
from bot.keyboards.keyboards import main_menu, request_response_kb
from bot.config import BOT_TOKEN

router = Router()


@router.message(F.text == "📬 Входящие запросы")
async def show_incoming_requests(message: Message):
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала зарегистрируйся! /start")
            return

        requests = await get_pending_requests_for_user(session, user.id)

        if not requests:
            await message.answer("📭 Входящих запросов нет.", reply_markup=main_menu)
            return

        senders_data = [
            (req.id, req.sender.display_profile(show_contacts=False))
            for req in requests
        ]

    await message.answer(
        f"📬 У тебя *{len(senders_data)}* входящих запроса(ов):",
        parse_mode="Markdown",
    )
    for req_id, profile_text in senders_data:
        await message.answer(
            profile_text,
            reply_markup=request_response_kb(req_id),
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("accept:"))
async def accept_request(callback: CallbackQuery):
    req_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(
            select(ConnectRequest)
            .options(
                selectinload(ConnectRequest.sender),
                selectinload(ConnectRequest.receiver),
            )
            .where(ConnectRequest.id == req_id)
        )
        req = result.scalar_one_or_none()

        if not req or req.status != "pending":
            await callback.answer("Запрос уже обработан.", show_alert=True)
            return

        await update_request_status(session, req, "accepted")

        sender_tg_id = req.sender.telegram_id
        sender_name = req.sender.name
        sender_username = req.sender.username
        receiver_name = req.receiver.name
        receiver_username = req.receiver.username

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=sender_tg_id,
            text=(
                f"🎉 *{receiver_name}* принял(а) твой запрос!\n\n"
                f"{'✉️ @' + receiver_username if receiver_username else '✉️ username скрыт'}"
            ),
            parse_mode="Markdown",
        )
        await bot.session.close()
    except Exception:
        pass

    await callback.answer("✅ Запрос принят!", show_alert=True)
    await callback.message.edit_text(
        f"✅ Вы теперь знакомы с *{sender_name}*!\n\n"
        f"{'✉️ @' + sender_username if sender_username else '✉️ username скрыт'}",
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("decline:"))
async def decline_request(callback: CallbackQuery):
    req_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        result = await session.execute(
            select(ConnectRequest).where(ConnectRequest.id == req_id)
        )
        req = result.scalar_one_or_none()

        if not req or req.status != "pending":
            await callback.answer("Запрос уже обработан.", show_alert=True)
            return

        await update_request_status(session, req, "declined")

    await callback.answer("Запрос отклонён.", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)


@router.message(F.text == "🤝 Мои знакомства")
async def show_my_connects(message: Message):
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала зарегистрируйся! /start")
            return

        connects = await get_accepted_connects(session, user.id)

        if not connects:
            await message.answer(
                "😔 У тебя пока нет знакомств.\n\nИщи людей через «🔍 Найти по исполнителю»!",
                reply_markup=main_menu,
            )
            return

        user_id = user.id
        lines = [f"🤝 *Твои знакомства ({len(connects)}):*\n"]
        for req in connects:
            other = req.receiver if req.sender_id == user_id else req.sender
            contact = f"@{other.username}" if other.username else "username скрыт"
            lines.append(f"• *{other.name}* — {contact}\n  🎵 {other.artists}")

    await message.answer(
        "\n".join(lines), parse_mode="Markdown", reply_markup=main_menu
    )
