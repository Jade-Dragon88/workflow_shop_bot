from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
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
    user_id = message.from_user.id
    username = message.from_user.username
    
    # --- Register user in the database ---
    try:
        # Check if user already exists using our new HTTP client
        existing_users = await supabase_http_client.select(
            table="users",
            params={"telegram_id": f"eq.{user_id}", "select": "telegram_id"}
        )
        
        if not existing_users:
            # User does not exist, insert them
            logging.info(f"New user: {username} ({user_id}). Registering...")
            user_data = {
                'telegram_id': user_id,
                'username': username,
                'registered_at': User().registered_at.isoformat(),
            }
            await supabase_http_client.insert(table="users", data=user_data)
            logging.info(f"User {username} ({user_id}) registered successfully.")
        else:
            logging.info(f"User {username} ({user_id}) is already registered.")
            
    except Exception as e:
        logging.error(f"Error during user registration for {username} ({user_id}): {e}", exc_info=True)

    # Send welcome message
    welcome_text = (
        "<b>Welcome to the n8n Workflows Shop!</b>\n\n"
        "Here you can find ready-made solutions for server monitoring and automation.\n\n"
        "Select an option from the menu below to get started:"
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
        "<b>Bot Help & Information</b>\n\n"
        "This bot allows you to purchase n8n workflows for server monitoring.\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Show the main menu\n"
        "/catalog - View the list of available workflows\n"
        "/help - Show this help message\n\n"
        "For support, please use the /support command or contact the administrator."
    )
    await message.answer(text=help_text)

# This handler is for the "Back to Main Menu" button in other sections
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """
    Handles the 'main_menu' callback, returning the user to the main menu.
    """
    menu_text = "You are back in the main menu. What would you like to do?"
    await callback.message.edit_text(
        text=menu_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()
