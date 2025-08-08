import asyncio
import logging
import sys
from os import path
from aiogram import Bot, Dispatcher

# Импортируем конфигурацию и все обработчики
from config import API_TOKEN, DB_NAME
from database import create_tables
from handlers import router as main_router


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout
)


async def main():
    """
    Основная функция для запуска бота.
    """
    # Создаем экземпляр бота
    bot = Bot(token=API_TOKEN)

    # Удаляем вебхук, если он был установлен
    await bot.delete_webhook()
    await asyncio.sleep(0.1)  # небольшая пауза для гарантии

    # Создаем экземпляр диспетчера
    dp = Dispatcher()
    
    # Подключаем роутер с обработчиками
    dp.include_router(main_router)
    
    # Проверяем и создаем таблицы в базе данных, если они еще не существуют
    if not path.exists(DB_NAME):
        await create_tables(DB_NAME)

    # Запускаем процесс пулинга
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Запуск асинхронной функции main
    asyncio.run(main())
