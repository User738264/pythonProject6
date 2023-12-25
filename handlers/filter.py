from typing import Any, Dict, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.fsm.storage.redis import RedisStorage

from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
)


sub_channel = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Канал', url='https://t.me/test_chat_i')
        ]
    ]

)


class CheckSubscription(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        chat_member = await event.bot.get_chat_member('@test_chat_i', event.from_user.id)
        if chat_member.status == 'left':
            await event.answer("Подпишись на канал", reply_markup=sub_channel)
        else:
            return await handler(event, data)


