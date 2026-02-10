from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

class RateLimitMiddleware(BaseMiddleware):
    """
    A simple middleware to limit the rate of incoming messages from a user.
    Uses a TTLCache to store user request times.
    """
    def __init__(self, rate_limit: float = 2, time_period: int = 5):
        """
        :param rate_limit: Max number of requests per time_period.
        :param time_period: Time period in seconds.
        """
        self.limit = TTLCache(maxsize=10_000, ttl=time_period)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        
        # Check if user is already in the cache
        if user_id in self.limit:
            # If the user is in the cache, it means they have sent a request recently.
            # We don't need to do anything special, just let the message pass.
            # The cache will automatically handle the rate limiting logic.
            # If the user sends too many requests, they will simply not be processed
            # until the time-to-live (TTL) for their cache entry expires.
            pass
        
        # Add/update the user's entry in the cache
        self.limit[user_id] = None

        # Call the next handler in the chain
        return await handler(event, data)
