import aiosqlite
from config import DB_PATH

async def get_verse(surah_id: int, verse_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM verses WHERE surah_id = ? AND verse_id = ?",
            (surah_id, verse_id)
        ) as cursor:
            return await cursor.fetchone()

async def get_all_surahs():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT DISTINCT surah_id, surah_name_uz, surah_name_ar FROM verses ORDER BY surah_id"
        ) as cursor:
            return await cursor.fetchall()

async def get_surah_info(surah_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT surah_name_uz, surah_name_ar, MAX(verse_id) as total_verses FROM verses WHERE surah_id = ?",
            (surah_id,)
        ) as cursor:
            return await cursor.fetchone()

# ==========================================
# YANGI: Foydalanuvchi joylashuvini saqlash
# ==========================================
async def save_user_location(user_id: int, lat: float, lon: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, latitude, longitude) VALUES (?, ?, ?)",
            (user_id, lat, lon)
        )
        await db.commit()

# YANGI: Namoz vaqtini ko'rsatish uchun foydalanuvchi manzilini olish
async def get_user_location(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT latitude, longitude FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            return await cursor.fetchone()
