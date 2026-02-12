import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS

router = Router()

# This is the most idiomatic way to check for admins in aiogram 3.x
# We combine the Command filter with a "magic" filter F.
IS_ADMIN = F.from_user.id.in_(ADMIN_IDS)

@router.message(Command("admin"), IS_ADMIN)
async def cmd_admin_panel(message: Message):
    """
    Handles the /admin command, showing the main admin panel.
    """
    logging.info(f"Admin user {message.from_user.id} accessed the admin panel.")
    
    admin_text = (
        "<b>Панель администратора</b>\n\n"
        "Добро пожаловать! Выберите одну из доступных команд:\n"
        "/stats - Показать статистику\n"
        "/ban [user_id] [причина] - Забанить пользователя\n"
        "/unban [user_id] - Разбанить пользователя\n"
    )
    await message.answer(admin_text)

# This handler will catch attempts by non-admins to use admin commands.
# It should be registered for specific admin commands.
# The `~IS_ADMIN` part means "user is NOT an admin".
@router.message(Command("admin", "stats", "ban", "unban"), ~IS_ADMIN)
async def cmd_access_denied(message: Message):
    """
    Handles attempts by non-admins to use admin commands.
    """
    logging.warning(f"User {message.from_user.id} tried to use an admin command: {message.text}")
    await message.answer("У вас нет доступа к этой команде.")
