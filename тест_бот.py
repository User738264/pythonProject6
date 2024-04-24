import sqlite3
from typing import Any, Optional, List, Type
from aiogram import BaseMiddleware, loggers
from aiogram.client.session.middlewares.base import NextRequestMiddlewareType, BaseRequestMiddleware
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.methods import GetUpdates
from aiogram.methods.base import TelegramType, TelegramMethod, Response
from dotenv import load_dotenv, find_dotenv, dotenv_values
import os
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
)
from handlers import routers, users_mailing
from handlers.filter import CheckSubscription
load_dotenv(find_dotenv('data'))

chat_ids_and_their_links = {}
bot = Bot(token=os.getenv('TOKEN'), parse_mode=ParseMode.HTML)
dp = Dispatcher()

dp.message.middleware(CheckSubscription())


class RequestLogging(BaseRequestMiddleware):
    def __init__(self, ignore_methods: Optional[List[Type[TelegramMethod[Any]]]] = None):
        """
        Middleware for logging outgoing requests

        :param ignore_methods: methods to ignore in logging middleware
        """
        self.ignore_methods = ignore_methods if ignore_methods else []

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: "Bot",
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        if type(method) not in self.ignore_methods:
            loggers.middlewares.info(
                "Make request with method=%r by bot id=%d",
                type(method).__name__,
                bot.id,
            )
        return await make_request(bot, method)


bot.session.middleware(RequestLogging(ignore_methods=[GetUpdates]))
dp.include_router(routers.form_router)
dp.include_router(users_mailing.admin_router)


async def main():
    # Запускаем бота в полинге
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    # Запускаем асинхронный код для запуска бота
    asyncio.run(main())
