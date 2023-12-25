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

form_router = Router()
bot = Bot(token=os.getenv('TOKEN'), parse_mode=ParseMode.HTML)
groups_id = (os.getenv('ID_GROUP1'), os.getenv('ID_GROUP2'), os.getenv('ID_GROUP3'), os.getenv('ID_GROUP4'),
             os.getenv('ID_GROUP5'))
keys = []
for i in range(14):
    keys.append(os.getenv(f'API_KEY{i}'))
keys_counter = 0
flag = False
history = sqlite3.connect('history.db')
cursor = history.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
orderid INT PRIMARY KEY,
chat TEXT NOT NULL,
message TEXT NOT NULL,
problem TEXT NOT NULL,
data TEXT NOT NULL
)
''')
history.commit()
history.close()


indeficators = []
a = sqlite3.connect('users.db')
cur = a.cursor()
tasks = cur.execute('''SELECT password from Exercise''').fetchall()
a.commit()
a.close()
for i in tasks:
    indeficators.append(i[0])


class Form(StatesGroup):
    reg_answer = State()
    waiting_answer = State()
    waiting_task = State()
    waiting_mail = State()


@form_router.message(CommandStart())
async def command_registration(message: Message, state: FSMContext) -> None:
    if str(message.from_user.id) in list(chat_ids_and_their_links.keys()):
        await message.answer("Вы уже зарегистрированы.")
    else:
        await state.set_state(Form.reg_answer)
        await message.answer(
            "Введите айди своей группы",
            reply_markup=ReplyKeyboardRemove(),
        )


@form_router.message(Form.reg_answer)
async def waiting_for_group_id(message: Message, state: FSMContext) -> None:
    admins = sqlite3.connect('data/admins.db')
    a = admins.cursor()
    groups = a.execute('''SELECT qwerty FROM Admins''').fetchall()
    groups = [i[0] for i in groups]
    if message.text in groups:
        await message.answer(
            "Вы успешно зарегистрировались!\nВы можете разослать проблему, используя команду /question",
            reply_markup=ReplyKeyboardRemove(),
        )
        tg_link = 'https://t.me/' + message.from_user.username
        chat_ids_and_their_links[str(message.from_user.id)] = tg_link
        u = sqlite3.connect('users.db')
        cursor = u.cursor()
        cursor.execute('INSERT INTO System (user, link, qwerty) VALUES (?, ?, ?)',
                       (str(message.from_user.id), tg_link, message.text))
        u.commit()
        u.close()
        values_list = rating_sheet.col_values(1)
        if tg_link not in values_list:
            rating_sheet.update(f'A{len(values_list) + 1}', tg_link)
            rating_sheet.update(f'B{len(values_list) + 1}', '0')
        await state.clear()
    else:
        await bot.send_message(message.from_user.id, 'Похоже, вы допустили ошибку. Попробуйте ещё раз!')


@form_router.callback_query(lambda query: query.data == 'YES')
async def process_button(query: types.CallbackQuery):
    global date, time, questions_text, questions_id, user_id, user_name, user_link, user_who_answer, answer_rating
    try:
        await bot.delete_message(query.from_user.id, query.message.message_id)
        await bot.send_message(query.from_user.id, 'Ваше сообщение отправлено!')
        values = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='тест' + "!A1",
            valueInputOption="RAW",
            body={
                'values': [
                    [date, time, questions_text, questions_id, user_id, user_name, user_link, '---', '---'],  # строка
                ]
            }).execute()
        await bot_sending_problems_to_another_chat(query.from_user.id)
    except:
        pass


@form_router.callback_query(lambda query: query.data == 'NO')
async def NO_button(query: types.CallbackQuery):
    global flag
    flag = False
    await bot.send_message(query.from_user.id, 'Отправьте свою проблему ещё раз.')
    await bot.delete_message(query.from_user.id, query.message.message_id)
    con = sqlite3.connect('history.db')  # тоже, но только из БД
    cur = con.cursor()
    result = cur.execute("""DELETE FROM Users
                        WHERE 
                            chat LIKE ?
                        """, (query.from_user.id,)).fetchall()
    con.commit()
    con.close()


async def bot_sending_problems_to_another_chat(user_who_send_problem):
    global flag
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='Ответить', callback_data=user_who_send_problem))
    group_id = chat_ids_and_their_links[str(user_who_send_problem)][1]
    for id, link in chat_ids_and_their_links.items():
        # if False:
        if id == str(user_who_send_problem) or group_id != link[1]:
            pass
        else:
            try:
                msg = await bot.send_message(id, f'Нужна помощь!\nПроблема: {problem}',
                                             reply_markup=builder.as_markup())
                history = sqlite3.connect('history.db')
                cursor = history.cursor()
                cursor.execute('INSERT INTO Users (chat, message, problem, data) VALUES (?, ?, ?, ?)',
                               (id, msg.message_id, questions_id, str(datetime.datetime.now())))
                history.commit()
                history.close()
            except:
                await bot.send_message(id, 'Кто-то другой уже успел ответить!')
    flag = False


@form_router.callback_query(lambda callback_query: callback_query.data not in ('YES', 'NO', '0', '1', '2', '3', '4',
                                                                               '5', 'Мне помогли!', 'a', 'b', 'c', 'd',
                                                                               'e', 'f', 'g', 'i', 'j',
                                                                               'ABCDABCDAQWEQWEQWEQWEQWE')
                                                   and callback_query.data not in indeficators)
async def answer_process(query: types.CallbackQuery):
    global flag
    # достаёт айдишники у сообщений
    reading = ws.col_values(4)

    # перебирает список чатов, в которых удаляется сообщения
    for i, link in chat_ids_and_their_links.items():
        if i == query.data:
            pass
        else:
            try:
                con = sqlite3.connect('history.db')
                cur = con.cursor()
                result = cur.execute("""SELECT message, problem FROM Users
                        WHERE 
                            chat LIKE ?
                        """, (i,)).fetchall()  # достаёт сообщения с просьбой о помощи и саму проблему
                con.commit()
                con.close()
                for msg_id in result:
                    await bot.delete_message(i, msg_id[0])  # удаляет просьбу о помощи у всех пользователей
                    con = sqlite3.connect('history.db')  # тоже, но только из БД
                    cur = con.cursor()
                    result = cur.execute("""DELETE FROM Users
                    WHERE 
                        message LIKE ?
                    """, (msg_id[0],)).fetchall()
                    con.commit()
                    con.close()
                    row = reading.index(str(msg_id[1]))  # записывает ответевшего в гугл таблицу
                    ws.update(f'H{row + 1}', query.from_user.username)
            except:
                pass

    await bot.send_message(query.from_user.id, f'Помогите пользователю:\n{chat_ids_and_their_links[query.data][0]}')
    await bot.send_message(query.data,
                           f'Вам помогает пользователь:\n{chat_ids_and_their_links[str(query.from_user.id)][0]}\nНе забудьте оценить ответ!')
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='Мне помогли!', callback_data='Мне помогли!'),
                )
    await bot.send_message(query.data, 'Нажмите, когда вам помогут!', reply_markup=builder.as_markup(),
                           parse_mode="Markdown")


@form_router.callback_query(lambda callback_query: callback_query.data == "Мне помогли!")
async def rating(query: types.CallbackQuery):
    await bot.delete_message(query.from_user.id, query.message.message_id)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text='0', callback_data='0'),
                types.InlineKeyboardButton(text='1', callback_data='1'),
                types.InlineKeyboardButton(text='2', callback_data='2'),
                types.InlineKeyboardButton(text='3', callback_data='3'),
                types.InlineKeyboardButton(text='4', callback_data='4'),
                types.InlineKeyboardButton(text='5', callback_data='5'),
                )
    await bot.send_message(query.from_user.id, 'Оцените качество помощи', reply_markup=builder.as_markup(),
                           parse_mode='Markdown')


@form_router.callback_query(
    lambda callback_query: callback_query.data == '0' or callback_query.data == '1' or callback_query.data == '2' or callback_query.data == '3' or callback_query.data == '4' or callback_query.data == '5')
async def rating(query: types.CallbackQuery):
    await bot.delete_message(query.from_user.id, query.message.message_id)
    await bot.send_message(query.from_user.id, 'Ваша оценка ответа обработана')
    reading = ws.col_values(5)
    row = len(reading) - list(reversed(reading)).index(str(query.from_user.id))
    ws.update(f'I{row}', query.data)
    reading = ws.col_values(8)
    user_who_answer = 'https://t.me/' + reading[row - 1]
    values_list = rating_sheet.col_values(1)
    values_list_for_sort = list(map(int, rating_sheet.col_values(2)[1:]))
    values_list_for_sort.sort()
    row = values_list.index(user_who_answer)
    values_list = rating_sheet.col_values(2)
    rating_sheet.update(f'B{row + 1}', str(int(query.data) + int(values_list[row])))
    await bot.send_message(get_key(chat_ids_and_their_links, user_who_answer),
                           f'Ваш ответ {query.from_user.username} оценили на {query.data} {some_dict[query.data]}\n'
                           f'Текущее количество баллов: {int(query.data) + int(values_list[row])}'
                           f'\nВаше место в рейтинге: {values_list_for_sort.index(int(query.data) + int(values_list[row])) + 1}')
    if query.data == '0':
        await bot.send_message(get_key(chat_ids_and_their_links, user_who_answer), 'Если оценка ответа вас не '
                                                                                   'устраивает, то можете обратиться в '
                                                                                   'техподдержку\nhttps://t.me/high_tech_12')


@form_router.message(Command("question"))
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.waiting_answer)
    await message.answer(
        "Привет! Какая у вас проблема?",
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Form.waiting_answer)
async def process_name(message: Message, state: FSMContext) -> None:
    global problem, date, time, questions_text, questions_id, user_id, user_name, user_link, user_who_answer, answer_rating
    global chat_id, flag
    if flag:
        await message.answer(
            'Извините, в данный момент мы обрабатываем другой запрос.\nПопробуйте буквально через секунд двадцать', )
    else:
        flag = True
        await state.update_data(name=message.text)
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text='Да', callback_data="YES"),
                    types.InlineKeyboardButton(text='Нет', callback_data="NO")
                    )
        await message.answer(
            "Подтвердить отправку сообщения?",
            reply_markup=builder.as_markup()
        )
        problem = message.text
        dt = str(datetime.datetime.now()).split(' ')
        chat_id = message.chat.id
        date, time, questions_text, questions_id, user_id, user_name, user_link, = \
            dt[0], dt[1][
                   :-7], message.text, message.message_id, message.from_user.id, message.from_user.first_name, 'https://t.me/' + message.from_user.username,


@form_router.message(Command("generate_exercise"))
async def generate_exercise(message: Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='Переменные, Комментарии, print()', callback_data="a"),
                types.InlineKeyboardButton(text='input, Арифметические операции, Пакет math', callback_data="b"),
                types.InlineKeyboardButton(text='Типы данных, Операторы сравнения', callback_data="c"),
                types.InlineKeyboardButton(text='Условные операторы if, and, or, not', callback_data="d"),
                types.InlineKeyboardButton(text='Циклы While', callback_data="e"),
                types.InlineKeyboardButton(text='for…in, Списки', callback_data="f"),
                types.InlineKeyboardButton(text='continue, break', callback_data="g"),
                types.InlineKeyboardButton(text='Функции', callback_data="i"),
                types.InlineKeyboardButton(text='Параметры и аргументы функций', callback_data="j"),
                width=1
                )
    await message.answer(
        "Сгенерировать задание",
        reply_markup=builder.as_markup()
    )


async def ai_generate_exercise(prompt, message):
    input_usr_message = prompt
    global keys_counter
    try:
        client = OpenAI(
            api_key=keys[keys_counter],
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": 'Будь помощником!'},
                {
                    "role": "user",
                    "content": input_usr_message,
                }
            ],
            model="gpt-3.5-turbo",
        )
        bot_reply = chat_completion.choices[0].message.content
        if prompt[:62] == 'Сгенерируй задачу по програмированию на языке Python по теме: ':
            a = sqlite3.connect('users.db')
            cur = a.cursor()
            indeficator = get_indeficator()
            indeficators.append(indeficator)
            cur.execute('''INSERT INTO Exercise (user, task, prompt, password) VALUES (?, ?, ?, ?)''',
                        (message.chat.id, prompt[62:], bot_reply, indeficator))
            a.commit()
            a.close()
        await message.reply(bot_reply, parse_mode=ParseMode.MARKDOWN)
    except:
        print(keys[keys_counter])
        keys_counter += 1
        if keys_counter > len(keys):
            keys_counter = 0
        await ai_generate_exercise(prompt, message)


@form_router.callback_query(lambda callback_query: callback_query.data in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'i', 'j'])
async def ai_send_exercise(query: types.CallbackQuery):
    await ai_generate_exercise(
        f'Сгенерируй задачу по програмированию на языке Python по теме: {exercise_dict[query.data]}\nНе стоит писать '
        f'мне решения задачи', query.message)


@form_router.message(Command('check_task'))
async def ai_check_task(message: Message):
    a = sqlite3.connect('users.db')
    cur = a.cursor()
    tasks = cur.execute('''SELECT user, task, prompt, password from Exercise 
                 WHERE user LIKE ?''', (message.from_user.id,)).fetchall()
    a.commit()
    a.close()
    if len(tasks) == 0:
        await bot.send_message(message.from_user.id, 'У вас нет никаких заданий!')
    else:
        builder = InlineKeyboardBuilder()
        for i in tasks:
            builder.row(types.InlineKeyboardButton(text=i[1], callback_data=i[3]))
        await message.answer(
            "Выберите задание, которое надо проверить",
            reply_markup=builder.as_markup()
        )


@form_router.callback_query(lambda callback_query: callback_query.data in indeficators)
async def check(query: types.CallbackQuery, state: FSMContext) -> None:
    a = sqlite3.connect('users.db')
    cur = a.cursor()
    cur.execute('''UPDATE Exercise SET state = ? 
                WHERE user LIKE ?''', ('0', query.message.chat.id,))
    cur.execute('''UPDATE Exercise SET state = ? 
                WHERE password LIKE ?''', ('1', query.data,))
    task = cur.execute('''SELECT prompt FROM Exercise
                       WHERE password LIKE ?''', (query.data,)).fetchall()
    a.commit()
    a.close()
    await state.set_state(Form.waiting_task)
    await bot.send_message(query.message.chat.id, task[0][0])
    await bot.send_message(query.message.chat.id, 'Напишите ваше решение задачи')


@form_router.message(Form.waiting_task)
async def process_name(message: Message, state: FSMContext) -> None:
    a = sqlite3.connect('users.db')
    cur = a.cursor()
    tasks = cur.execute('''SELECT user, task, prompt from Exercise 
                     WHERE user LIKE ? and state LIKE ?''', (message.from_user.id, '1',)).fetchall()
    a.commit()
    a.close()
    await ai_generate_exercise(
        f'Проверь моё решение задачи по Python. Это условие: {tasks[-1][2]}\nЭто моё решение: {message.text}', message)


@form_router.message(Command('clear_task'))
async def ai_check_task(message: Message):
    a = sqlite3.connect('users.db')
    cur = a.cursor()
    cur.execute('''DELETE FROM Exercise 
                   WHERE user LIKE ?''', (message.from_user.id,))
    a.commit()
    a.close()
    await bot.send_message(message.from_user.id, 'Ваши задачи очищены')
