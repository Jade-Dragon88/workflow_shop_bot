from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

# Assuming Workflow is defined somewhere, for type hinting.
# In a real scenario, you'd import it from database.models
class Workflow:
    slug: str
    name: str
    price: float

def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру для главного меню.
    Adds an admin button if the user is an admin.
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

    if is_admin:
        keyboard.append([
            InlineKeyboardButton(text="⚙️ Админка", callback_data="admin_panel")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_catalog_keyboard() -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for the main catalog view, showing only categories.
    """
    buttons = []
    
    # Priority filters (Categories)
    buttons.append([
        InlineKeyboardButton(text="❗️ Крайне важные", callback_data="filter_priority:1")
    ])
    buttons.append([
        InlineKeyboardButton(text="👍 Рекомендуемые", callback_data="filter_priority:2")
    ])
    buttons.append([
        InlineKeyboardButton(text="ℹ️ Общая информация", callback_data="filter_priority:3")
    ])
    buttons.append([
        InlineKeyboardButton(text="🗂️ Все Workflows", callback_data="filter_priority:all")
    ])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_filtered_catalog_keyboard(workflows: List[Workflow], price: int) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for a filtered catalog view, showing a consistent price.
    """
    buttons = []
    for wf in workflows:
        # Use the single dynamic price for all items in this view
        button_text = f"{wf.name} - {price:.0f}₽"
        callback_data = f"workflow:{wf.slug}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])

    # The "Back" button should now lead to the main catalog view
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_workflow_card_keyboard(slug: str, price: float) -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру для карточки workflow.
    """
    keyboard = [
        [InlineKeyboardButton(text=f"💳 Купить за {price:.0f}₽", callback_data=f"buy:{slug}")],
        [InlineKeyboardButton(text="⬅️ Назад в каталог", callback_data="catalog_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    Creates the keyboard for the main admin panel.
    Uses text to indicate the danger level of buttons.
    """
    buttons = [
        [InlineKeyboardButton(text="🔄 Отправить файл", callback_data="admin:send_file")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin:change_price")],
        [InlineKeyboardButton(text="🚫 Забанить (Опасно)", callback_data="admin:ban_user")],
        [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

