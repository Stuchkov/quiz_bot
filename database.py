import aiosqlite

async def create_tables(db_name: str):
    """
    Создает все необходимые таблицы (quiz_state и quiz_results).
    Добавляет столбец 'score' в таблицу quiz_state, если его нет.
    """
    async with aiosqlite.connect(db_name) as db:
        # Таблица для отслеживания текущего состояния квиза
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (
            user_id INTEGER PRIMARY KEY,
            question_index INTEGER,
            score INTEGER DEFAULT 0
        )''')
        # Таблица для сохранения последнего результата пользователя
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_results (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            score INTEGER
        )''')
        
        # Проверяем, существует ли столбец 'score' в таблице quiz_state,
        # и добавляем его, если он отсутствует.
        async with db.execute("PRAGMA table_info(quiz_state)") as cursor:
            columns = [column[1] for column in await cursor.fetchall()]
            if 'score' not in columns:
                await db.execute('''ALTER TABLE quiz_state ADD COLUMN score INTEGER DEFAULT 0''')
                
        await db.commit()

async def get_quiz_state(db_name: str, user_id: int) -> tuple[int, int]:
    """
    Получает текущий индекс вопроса и счет для пользователя.
    Возвращает (0, 0), если пользователь не найден.
    """
    async with aiosqlite.connect(db_name) as db:
        async with db.execute('SELECT question_index, score FROM quiz_state WHERE user_id = (?)', (user_id,)) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0], results[1]
            else:
                return 0, 0

async def update_quiz_state(db_name: str, user_id: int, index: int, score: int):
    """
    Обновляет или вставляет текущий индекс вопроса и счет для пользователя.
    """
    async with aiosqlite.connect(db_name) as db:
        await db.execute(
            'INSERT OR REPLACE INTO quiz_state (user_id, question_index, score) VALUES (?, ?, ?)',
            (user_id, index, score)
        )
        await db.commit()

async def save_quiz_result(db_name: str, user_id: int, username: str, score: int):
    """
    Сохраняет последний результат прохождения квиза для пользователя.
    """
    async with aiosqlite.connect(db_name) as db:
        await db.execute(
            'INSERT OR REPLACE INTO quiz_results (user_id, username, score) VALUES (?, ?, ?)',
            (user_id, username, score)
        )
        await db.commit()

async def get_leaderboard(db_name: str):
    """
    Получает список 10 лучших результатов всех игроков.
    """
    async with aiosqlite.connect(db_name) as db:
        async with db.execute('SELECT username, score FROM quiz_results ORDER BY score DESC LIMIT 15') as cursor:
            results = await cursor.fetchall()
            return results
