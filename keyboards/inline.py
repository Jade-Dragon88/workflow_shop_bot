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

def get_catalog_keyboard(workflows: List[Workflow]) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard with a list of workflows.
    """
    buttons = []
    for wf in workflows:
        # Each workflow gets its own button
        button_text = f"{wf.name} - {wf.price:.0f}₽"
        callback_data = f"workflow:{wf.slug}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Add navigation buttons
    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
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
