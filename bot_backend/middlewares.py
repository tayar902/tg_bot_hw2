from aiogram import BaseMiddleware
from aiogram.types import Message
from config import aiohttp_logger
import logging

logger = logging.getLogger("aiohttp_logger")
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        logger.info(f"Получено сообщение: {event.text}")
        return await handler(event, data)
