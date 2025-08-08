from aiogram import types, Router, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import re

from config import DB_NAME
from database import get_quiz_state, update_quiz_state, save_quiz_result, get_leaderboard
from quiz_data import quiz_data
from quiz_logic import generate_options_keyboard


# Создаем роутер для регистрации обработчиков
router = Router()


# Функция для экранирования символов Markdown в строке
def escape_markdown(text: str) -> str:
    """Экранирует специальные символы Markdown."""
    # Список специальных символов, которые нужно экранировать
    # Добавляем символ \ перед каждым из них
    return re.sub(r'([_*[\]()~`>#+-=|{}.!])', r'\\\1', text)


async def get_question(message: types.Message, user_id: int, username: str):
    """
    Отправляет пользователю следующий вопрос квиза.
    """
    # Получаем текущий индекс вопроса и счет для пользователя
    current_question_index, score = await get_quiz_state(DB_NAME, user_id)
    
    # Если все вопросы пройдены
    if current_question_index >= len(quiz_data):
        # Сохраняем итоговый результат
        await save_quiz_result(DB_NAME, user_id, username, score)
        await message.answer(f"🎉 Квиз завершен! Ваш итоговый счёт: {score}/{len(quiz_data)}.")
        return

    # Получаем данные текущего вопроса
    question_data = quiz_data[current_question_index]
    correct_option = question_data['correct_option']
    options = question_data['options']
    
    # Генерируем клавиатуру с вариантами ответов
    keyboard = generate_options_keyboard(options, options[correct_option])
    
    await message.answer(
        f"{question_data['question']}",
        reply_markup=keyboard
    )


async def new_quiz(message: types.Message):
    """
    Начинает новый квиз для пользователя.
    """
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Сбрасываем индекс вопроса и счет в базе данных
    await update_quiz_state(DB_NAME, user_id, 0, 0)
    
    # Отправляем первый вопрос
    await get_question(message, user_id, username)


# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start.
    """
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="/stats"))
    await message.answer(
        "Добро пожаловать в квиз!",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


# Хэндлер на команду /quiz и кнопку "Начать игру"
@router.message(F.text == "Начать игру")
@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    """
    Обработчик команды /quiz или кнопки "Начать игру".
    """
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

# Хэндлер для вывода статистики
@router.message(F.text == "/stats")
@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """
    Обработчик команды /stats.
    Выводит таблицу лидеров.
    """
    leaderboard = await get_leaderboard(DB_NAME)
    if not leaderboard:
        await message.answer("Статистика пока пуста. Будьте первым, кто сыграет!")
        return

    stats_text = "🏆 **Таблица лидеров** 🏆\n\n"
    for i, (username, score) in enumerate(leaderboard):
        escaped_username = escape_markdown(username)
        stats_text += f"{i+1}. @{escaped_username}: {score} очков\n"
    
    await message.answer(stats_text, parse_mode='Markdown')


# Хэндлер на правильный ответ
@router.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    """
    Обработчик колбэка для правильного ответа.
    """
    current_question_index, current_score = await get_quiz_state(DB_NAME, callback.from_user.id)
    question_data = quiz_data[current_question_index]
    
    # Редактируем сообщение, удаляя кнопки
    await callback.message.edit_text(
        f"✅ Ваш ответ: {question_data['options'][question_data['correct_option']]}\n\n"
        f"Вопрос: {question_data['question']}"
    )

    # Обновляем состояние: увеличиваем индекс вопроса и счет
    await update_quiz_state(DB_NAME, callback.from_user.id, current_question_index + 1, current_score + 1)
    await get_question(callback.message, callback.from_user.id, callback.from_user.username)


# Хэндлер на неправильный ответ
@router.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    """
    Обработчик колбэка для неправильного ответа.
    """
    current_question_index, current_score = await get_quiz_state(DB_NAME, callback.from_user.id)
    question_data = quiz_data[current_question_index]
    correct_option = question_data['correct_option']
    
    # Редактируем сообщение, удаляя кнопки
    await callback.message.edit_text(
        f"❌ Неправильно.\n"
        f"Правильный ответ: {question_data['options'][correct_option]}\n\n"
        f"Вопрос: {question_data['question']}"
    )
    
    # Обновляем состояние: только увеличиваем индекс вопроса
    await update_quiz_state(DB_NAME, callback.from_user.id, current_question_index + 1, current_score)
    await get_question(callback.message, callback.from_user.id, callback.from_user.username)