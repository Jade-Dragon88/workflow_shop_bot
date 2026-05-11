from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramAPIError
from cachetools import TTLCache
import logging

class RateLimitMiddleware(BaseMiddleware):
    """
    A middleware to limit the rate of incoming messages from a user.
    Blocks users if they exceed the limit (10 requests per 60 seconds by default).
    """
    def __init__(self, rate_limit: int = 10, time_period: int = 60):
        """
        :param rate_limit: Max number of requests per time_period.
        :param time_period: Time period in seconds.
        """
        self.limit = rate_limit
        self.time_period = time_period
        self.cache = TTLCache(maxsize=10_000, ttl=time_period)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        
        current_count = self.cache.get(user_id, 0)
        
        if current_count >= self.limit:
            remaining = self.time_period
            try:
                await event.answer(
                    f"⚠️ Слишком много запросов! Подождите {remaining} секунд.",
                    show_alert=True
                )
            except TelegramAPIError:
                pass
            logging.warning(f"Rate limit exceeded for user {user_id}")
            return
        
        self.cache[user_id] = current_count + 1
        
        return await handler(event, data)
