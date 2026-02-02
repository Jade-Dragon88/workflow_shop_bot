from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Returns the inline keyboard for the main menu.
    """
    keyboard = [
        [
            InlineKeyboardButton(text="️ Каталог", callback_data="catalog_menu")
        ],
        [
            InlineKeyboardButton(text="? Поддержка", callback_data="support_menu"),
            InlineKeyboardButton(text="? Профиль", callback_data="profile_menu") # Placeholder
        ],
        [
            InlineKeyboardButton(text="? О боте", callback_data="about_bot")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
