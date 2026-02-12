import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS

router = Router()

# This is the most idiomatic way to check for admins in aiogram 3.x
# We combine the Command filter with a "magic" filter F.
IS_ADMIN = F.from_user.id.in_(ADMIN_IDS)

@router.callback_query(F.data == "admin_panel", IS_ADMIN)
async def cmd_admin_panel(callback: CallbackQuery):
    """
    Handles the "admin_panel" button, showing the main admin panel.
    """
    logging.info(f"Admin user {callback.from_user.id} accessed the admin panel via button.")
    
    admin_text = (
        "<b>Панель администратора</b>\n\n"
        "Добро пожаловать! Выберите одну из доступных команд:\n"
        "/stats - Показать статистику\n"
        "/ban [user_id] [причина] - Забанить пользователя\n"
        "/unban [user_id] - Разбанить пользователя\n"
    )
    # Answer the callback to remove the "loading" state on the button
    await callback.answer()
    # Send a new message with the admin panel
    await callback.message.answer(admin_text)

# This handler will catch attempts by non-admins to use admin commands.
@router.message(Command("stats", "ban", "unban"), ~IS_ADMIN)
async def cmd_access_denied(message: Message):
    """
    Handles attempts by non-admins to use admin commands.
    """
    logging.warning(f"User {message.from_user.id} tried to use an admin command: {message.text}")
    await message.answer("У вас нет доступа к этой команде.")
