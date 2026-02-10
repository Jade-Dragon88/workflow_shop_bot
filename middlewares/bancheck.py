from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import logging

from database.supabase_http_client import supabase_http_client

class BanCheckMiddleware(BaseMiddleware):
    """
    Middleware to check if a user is in the banned_users table.
    If the user is banned, it informs them and stops processing the update.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get('event_from_user')
        if not user:
            return await handler(event, data)

        # Allow callback queries for the support menu to pass through, even for banned users.
        if isinstance(event, CallbackQuery) and event.data == "support_menu":
            logging.info(f"Banned user {user.id} is accessing support. Allowing.")
            return await handler(event, data)

        user_id = user.id

        try:
            banned_user = await supabase_http_client.select(
                "banned_users", 
                params={"telegram_id": f"eq.{user_id}", "select": "telegram_id", "limit": 1}
            )

            if banned_user:
                logging.warning(f"Banned user {user_id} ({user.username}) tried to interact with the bot. Access denied.")
                # Inform the user about the ban and provide a support button
                bot: Bot = data['bot']
                await bot.send_message(
                    user_id, 
                    "Вы были заблокированы в этом боте. Для уточнения причин обратитесь в поддержку.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="💬 Поддержка", callback_data="support_menu")]
                    ])
                )
                # Stop processing the update
                return
        except Exception as e:
            logging.error(f"Error during ban check for user {user_id}: {e}")

        return await handler(event, data)
