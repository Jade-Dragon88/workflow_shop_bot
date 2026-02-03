from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

# Assuming Workflow is defined somewhere, for type hinting.
# In a real scenario, you'd import it from database.models
class Workflow:
    slug: str
    name: str
    price: float

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
        InlineKeyboardButton(text="👍 Рекомендуемые", callback_data="filter_priority:2"),
        InlineKeyboardButton(text="ℹ️ Общая информация", callback_data="filter_priority:3"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🗂️ Все Workflows", callback_data="filter_priority:all")
    ])

    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_filtered_catalog_keyboard(workflows: List[Workflow]) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard for a filtered catalog view, without filter buttons.
    """
    buttons = []
    for wf in workflows:
        button_text = f"{wf.name} - {wf.price:.0f}₽"
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
