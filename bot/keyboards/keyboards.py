from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Найти по исполнителю")],
        [
            KeyboardButton(text="👤 Мой профиль"),
            KeyboardButton(text="📬 Входящие запросы"),
        ],
        [KeyboardButton(text="🤝 Мои знакомства")],
    ],
    resize_keyboard=True,
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True,
)

skip_or_cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏭️ Пропустить")],
        [KeyboardButton(text="❌ Отмена")],
    ],
    resize_keyboard=True,
)

delete_or_cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🗑️ Удалить")],
        [KeyboardButton(text="❌ Отмена")],
    ],
    resize_keyboard=True,
)


def profile_actions_kb(target_tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💌 Отправить запрос на знакомство",
                    callback_data=f"send_req:{target_tg_id}",
                )
            ],
            [InlineKeyboardButton(text="➡️ Следующий", callback_data="next_result")],
        ]
    )


def request_response_kb(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"accept:{request_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"decline:{request_id}"
                ),
            ]
        ]
    )


edit_profile_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✏️ Изменить исполнителей", callback_data="edit:artists"
            )
        ],
        [InlineKeyboardButton(text="✏️ Изменить о себе", callback_data="edit:about")],
        [InlineKeyboardButton(text="✏️ Изменить группу", callback_data="edit:group")],
    ]
)
