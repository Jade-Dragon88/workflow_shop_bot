from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру для главного меню.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="💬 Поддержка", callback_data="support_menu"),
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="about_bot")
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile_menu") # Placeholder
        ],
        [
            InlineKeyboardButton(text="🗂️ Каталог", callback_data="catalog_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
