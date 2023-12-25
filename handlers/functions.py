import secrets
import string

import tiktoken as tiktoken


def get_key(d, value):
    for k, v in d.items():
        if v == value:
            return k


date, time, questions_text, questions_id, user_id, user_name, user_link, user_who_answer, answer_rating \
    = '', '', '', '', '', '', '', '', ''
some_dict = {'0': 'баллов', '1': 'балл', '2': 'балла', '3': 'балла', '4': 'балла', '5': 'баллов'}
exercise_dict = {'a': 'Переменные, Комментарии, print()', 'b': 'input, Арифметические операции, Пакет math',
                 'c': 'Типы данных, Операторы сравнения', 'd': 'Условные операторы if, and, or, not',
                 'e': 'Циклы While', 'f': 'for…in, Списки', 'g': 'continue, break', 'i': 'Функции',
                 'j': 'Параметры и аргументы функций'}


def get_indeficator():
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(20))
    return password
