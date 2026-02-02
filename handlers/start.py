from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from html import escape
import logging

from keyboards.inline import get_main_menu_keyboard
# Import functions needed for showing a workflow card
from handlers.catalog import get_workflow_by_slug, get_workflow_card_keyboard
from database.supabase_http_client import supabase_http_client
from database.models import User

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message, bot: Bot, command: CommandObject):
    """
    Handler for the /start command.
    - If a deep link slug is provided, it shows the corresponding workflow card.
    - Otherwise, it greets the user, registers them, and shows the main menu.
    """
    user = message.from_user
    user_id = user.id
    username = user.username
    first_name = escape(user.first_name)

    # --- Deep Link Handling ---
    if command.args:
        slug = command.args
        logging.info(f"User {username} ({user_id}) used deep link with slug: {slug}")
        
        workflow = await get_workflow_by_slug(slug)
        if workflow:
            # If workflow is found, show its card directly
            card_text = (
                f"📄 **{workflow.name}**\n\n"
                f"<b>Описание:</b> {workflow.description}\n\n"
                f"<b>Версия:</b> {workflow.version}\n"
                f"<b>Цена:</b> {workflow.price:.0f}₽"
            )
            await message.answer(
                text=card_text,
                reply_markup=get_workflow_card_keyboard(slug, workflow.price)
            )
            return # Stop further execution
        else:
            logging.warning(f"Deep link slug '{slug}' not found in database.")
            # Fall through to the default start message if slug is invalid

    # --- Standard Start & User Registration ---
    try:
        existing_users = await supabase_http_client.select(
            table="users",
            params={"telegram_id": f"eq.{user_id}", "select": "telegram_id"}
        )
        if not existing_users:
            logging.info(f"New user: {username} ({user_id}). Registering...")
            user_data = {
                'telegram_id': user_id, 'username': username,
                'registered_at': User(telegram_id=user_id).registered_at.isoformat(),
            }
            await supabase_http_client.insert(table="users", data=user_data)
            logging.info(f"User {username} ({user_id}) registered successfully.")
        else:
            logging.info(f"User {username} ({user_id}) is already registered.")
    except Exception as e:
        logging.error(f"Error during user registration for {username} ({user_id}): {e}", exc_info=True)

    # Send welcome message
    welcome_text = (
        f"👋 Привет, {first_name}!\n\n"
        "Здесь вы можете найти готовые решения для мониторинга и автоматизации серверов.\n\n"
        "Выберите опцию в меню ниже, чтобы начать:"
    )
    await message.answer(text=welcome_text, reply_markup=get_main_menu_keyboard())

@router.message(Command("help"))
async def handle_help(message: Message):
    """
    Handler for the /help command. Provides helpful information to the user.
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

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """
    Handles the 'main_menu' callback, returning the user to the main menu.
    """
    menu_text = "Вы вернулись в главное меню. Что бы вы хотели сделать?"
    await callback.message.edit_text(text=menu_text, reply_markup=get_main_menu_keyboard())
    await callback.answer()