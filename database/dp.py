import aiosqlite
from datetime import datetime
from datetime import datetime, timezone


DB_PATH = "C:/Users/user/Downloads/subscriber_manager/database/schedules.db"

async def init_db():
    """
    Инициализация базы данных.
    Создает таблицу deletion_schedule, если она не существует.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS deletion_schedule (
                job_id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                status TEXT DEFAULT 'scheduled',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()

async def add_deletion_schedule(user_name: list, scheduled_time: datetime, job_id: str):
    """
    Добавляет новую задачу удаления для каждого пользователя.
    
    :param user_names: список usernames (например, ["@user1", "@user2"])
    :param scheduled_time: время, когда должна сработать задача (datetime)
    :param job_id: идентификатор задачи в планировщике
    """
    async with aiosqlite.connect(DB_PATH) as db:
            created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            await db.execute("""
                INSERT INTO deletion_schedule (user_name, scheduled_time, status, job_id,created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_name, scheduled_time.strftime("%Y-%m-%d %H:%M:%S"), "scheduled", job_id,created_at))
            await db.commit()

async def update_schedule_status(job_id: int, new_status: str):
    """
    Обновляет статус задачи удаления по её job_id.
    
    :param job_id: идентификатор задачи (job_id)
    :param new_status: новый статус (например, "завершено" или "не удалось удалить")
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE deletion_schedule
            SET status = ?
            WHERE job_id = ?
        """, (new_status, job_id))
        await db.commit()

async def get_job_id_by_username(username: str) -> str:
    """
    Получает job_id для указанного username.
    
    :param username: имя пользователя, по которому ищем job_id
    :return: job_id (строка) или None, если не найдено
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT job_id FROM deletion_schedule 
            WHERE user_name = ? 
            ORDER BY scheduled_time DESC 
            LIMIT 1
        """, (username,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def cancel_schedule_by_username(username: str):
    """
    Удаляет задачи удаления для указанного username.
    
    :param username: имя пользователя, по которому удаляются задачи
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM deletion_schedule 
            WHERE user_name = ?
        """, (username,))
        await db.commit()

async def get_all_schedules():
    """
    Получает все запланированные задачи, отсортированные по scheduled_time.
    
    :return: список записей из таблицы deletion_schedule
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT * FROM deletion_schedule 
            ORDER BY scheduled_time ASC
        """) as cursor:
            return await cursor.fetchall()
        
async def get_schedule_status(job_id: str) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT status FROM deletion_schedule 
            WHERE job_id = ?
        """, (job_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None




async def clear_database():
    # Подключение к базе данных
    async with aiosqlite.connect(DB_PATH) as db:
        # Очистка таблицы
        # await db.execute("DELETE FROM expenses ")
        await db.execute("DROP TABLE IF EXISTS deletion_schedule ")
        await db.commit()  # Обязательно подтвердите изменения