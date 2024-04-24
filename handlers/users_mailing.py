import asyncio
import datetime
from random import randint

import openai
import tiktoken
from openai import OpenAI
import gspread
import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
from dotenv import load_dotenv, find_dotenv, dotenv_values
import os
from data.users_data import chat_ids_and_their_links
from data.sheet import rating_sheet, service, gc, ws, spreadsheet_id
from handlers.functions import get_key, some_dict, date, time, questions_text, questions_id, user_id, user_name, \
    user_link, user_who_answer, answer_rating, get_indeficator, exercise_dict
from handlers.routers import Form

admin_router = Router()
bot = Bot(token=os.getenv('TOKEN'), parse_mode=ParseMode.HTML)
ikb_menu = InlineKeyboardMarkup(row_width=1,
                                inline_keyboard=[
                                    [
                                        InlineKeyboardButton(text='➡️ ПЕРЕЙТИ ⬅️', url='https://t.me/high_tech_12')
                                    ],
                                ])
symbols = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz123456789'


@admin_router.message(Command("admin"))
async def cmd_start(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Сгенерировать группу")],
        [types.KeyboardButton(text="Разослать сообщение")],
         ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите опцию",
        one_time_keyboard=False)
    text = "Привет, чем могу помочь?"

    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@admin_router.message(lambda message: message.text == "Сгенерировать группу")
async def registration_group(message: Message):
    admins = sqlite3.connect('data/admins.db')
    a = admins.cursor()
    admins_and_their_groups = a.execute('''SELECT id, qwerty FROM Admins''').fetchall()
    groups = a.execute('''SELECT qwerty FROM Admins''').fetchall()
    groups = [i[0] for i in groups]
    print(groups, admins_and_their_groups)
    for i in admins_and_their_groups[0]:
        if str(message.from_user.username) in str(i):
            while 1:
                password = symbols[randint(0, 56)] + symbols[randint(0, 56)] + symbols[randint(0, 56)] + symbols[
                    randint(0, 56)]

                if password not in groups:
                    break
            await bot.send_message(message.from_user.id,
                                   f'{message.from_user.first_name}, идентификатор вашей группы:\n{password}')
            a.execute('''INSERT INTO Admins (id, qwerty) VALUES (?, ?)''', (str(message.from_user.username), password))
            admins.commit()


@admin_router.message(lambda message: message.text == "Разослать сообщение")
async def mailing(message: Message, state: FSMContext) -> None:
    admins = sqlite3.connect('data/admins.db')
    a = admins.cursor()
    admins_and_their_groups = a.execute('''SELECT id, qwerty FROM Admins''').fetchall()
    admins = [i[0] for i in admins_and_their_groups]
    if str(message.from_user.id) in admins:
        await state.set_state(Form.waiting_mail)
        await bot.send_message(message.from_user.id, 'Введите текст сообщения.')


@admin_router.message(Form.waiting_mail)
async def mailing_for_real(message: Message, state: FSMContext) -> None:
    await state.clear()
    a = sqlite3.connect('users.db')
    cur = a.cursor()
    users_to_mail = cur.execute('''SELECT user FROM System''',).fetchall()
    a.commit()
    a.close()
    for i in users_to_mail:
        try:
            if message.text:
                await bot.send_message(i[0], message.text)
            elif message.photo is not None:
                await bot.send_photo(i[0], photo=message.photo[-1].file_id,
                                     caption=message.caption)
            elif message.document is not None:
                await bot.send_document(i[0], document=message.document.file_id,
                                        caption=message.caption)
            elif message.sticker is not None:
                await bot.send_sticker(i[0], sticker=message.sticker.file_id)
            elif message.video is not None:
                await bot.send_video(i[0], video=message.video.file_id,
                                     caption=message.caption)
            elif message.audio is not None:
                await bot.send_audio(i[0], audio=message.audio.file_id,
                                     caption=message.caption)
        except:
            pass
