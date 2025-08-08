# Файл: quiz_logic.py
# Логика создания клавиатуры.

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from quiz_data import quiz_data

def generate_options_keyboard(answer_options: list, correct_answer: str) -> types.InlineKeyboardMarkup:
    """
    Генерирует инлайн-клавиатуру с вариантами ответов.
    """
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == correct_answer else "wrong_answer")
        )

    builder.adjust(1)  # Располагаем кнопки по одной в ряд
    return builder.as_markup()