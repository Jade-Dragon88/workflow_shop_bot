import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import BOT_TOKEN, LOGS_DIR
from handlers import start as start_handler
from utils.logger import setup_logger

async def main():
    """
    The main function that initializes and starts the bot.
    """
    # Initialize the bot with the token and default parse mode
    bot = Bot(token=BOT_TOKEN, default_parse_mode=ParseMode.HTML)
    
    # Initialize the dispatcher
    dp = Dispatcher()

    # --- Register Handlers ---
    # We will register handlers from different modules here
    dp.include_router(start_handler.router)
    
    # Start polling
    # Before starting, we drop all pending updates to avoid processing old messages
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Setup logger
    setup_logger(log_file_path=f"{LOGS_DIR}/bot.log")
    
    # Run the main async function
    try:
        logging.info("Starting the bot...")
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped manually.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
