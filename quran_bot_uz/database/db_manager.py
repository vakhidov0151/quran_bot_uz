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
import aiosqlite
from config import DB_PATH

# 1. Barcha duolarni bazadan olish
async def get_all_duas():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM duas") as cursor:
            return await cursor.fetchall()

# 2. Ma'lum bir duoni ID bo'yicha olish
async def get_dua_by_id(dua_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM duas WHERE id = ?", (dua_id,)) as cursor:
            return await cursor.fetchone()

# 3. Oyatlar orasidan matn bo'yicha qidirish (O'zbekcha tarjimasidan)
async def search_verses_by_text(keyword: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # LIKE operatori yordamida so'z qatnashgan oyatlarni qidiramiz
        async with db.execute(
            "SELECT * FROM verses WHERE text_uzbek LIKE ? LIMIT 10", 
            (f"%{keyword}%",)
        ) as cursor:
            return await cursor.fetchall()
