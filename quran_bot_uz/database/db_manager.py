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

# YANGI: Suraning jami oyatlar sonini aniqlovchi funksiya
async def get_surah_info(surah_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT surah_name_uz, surah_name_ar, MAX(verse_id) as total_verses FROM verses WHERE surah_id = ?",
            (surah_id,)
        ) as cursor:
            return await cursor.fetchone()