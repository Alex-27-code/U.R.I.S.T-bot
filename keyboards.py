from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Записаться")],
            [KeyboardButton(text="Моя запись"), KeyboardButton(text="Отменить запись")],
            [KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True
    )


def dates_keyboard(dates: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for date in dates:
        buttons.append([InlineKeyboardButton(text=date, callback_data=f"date:{date}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def times_keyboard(times: list[str], selected_date: str) -> InlineKeyboardMarkup:
    buttons = []
    for time in times:
        safe_time = time.replace(":", "_")
        buttons.append([
            InlineKeyboardButton(
                text=time,
                callback_data=f"time:{selected_date}:{safe_time}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_dates")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def gender_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def confirm_user_data_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Использовать сохранённые данные", callback_data="use_saved_data")],
            [InlineKeyboardButton(text="Ввести заново", callback_data="reenter_data")],
        ]
    )


def cancel_booking_keyboard(appointment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить отмену", callback_data=f"confirm_cancel:{appointment_id}")]
        ]
    )