from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from html import escape # Using Python's standard library for HTML escaping
import logging

from keyboards.inline import get_main_menu_keyboard
from database.supabase_http_client import supabase_http_client
from database.models import User

# All handlers for start commands and the main menu are here
router = Router()

@router.message(CommandStart())
async def handle_start(message: Message, bot: Bot):
    """
    Handler for the /start command.
    Greets the user, registers them in the database, and shows the main menu.
    """
    user = message.from_user
    user_id = user.id
    username = user.username
    # Escape the user's first name to prevent HTML injection issues
    first_name = escape(user.first_name)
    
    # --- Register user in the database ---
    try:
        existing_users = await supabase_http_client.select(
            table="users",
            params={"telegram_id": f"eq.{user_id}", "select": "telegram_id"}
        )
        
        if not existing_users:
            logging.info(f"New user: {username} ({user_id}). Registering...")
            user_data = {
                'telegram_id': user_id,
                'username': username,
                'registered_at': User(telegram_id=user_id).registered_at.isoformat(),
            }
            await supabase_http_client.insert(table="users", data=user_data)
            logging.info(f"User {username} ({user_id}) registered successfully.")
        else:
            logging.info(f"User {username} ({user_id}) is already registered.")
            
    except Exception as e:
        logging.error(f"Error during user registration for {username} ({user_id}): {e}", exc_info=True)

    # Send welcome message (without bold tags for now)
    welcome_text = (
        f"👋 Привет, {first_name}!\n\n"
        "Здесь вы можете найти готовые решения для мониторинга и автоматизации серверов.\n\n"
        "Выберите опцию в меню ниже, чтобы начать:"
    )
    
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def handle_help(message: Message):
    """
    Handler for the /help command.
    Provides helpful information to the user.
    """
    help_text = (
        "<b>ℹ️ Помощь и информация</b>\n\n"
        "Этот бот позволяет вам приобретать готовые n8n workflows для мониторинга серверов.\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Показать главное меню\n"
        "/catalog - Посмотреть каталог workflows\n"
        "/help - Показать это сообщение\n\n"
        "Для поддержки, пожалуйста, используйте команду /support или свяжитесь с администратором."
    )
    await message.answer(text=help_text)

# This handler is for the "Back to Main Menu" button in other sections
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """
    Handles the 'main_menu' callback, returning the user to the main menu.
    """
    menu_text = "Вы вернулись в главное меню. Что бы вы хотели сделать?"
    await callback.message.edit_text(
        text=menu_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
