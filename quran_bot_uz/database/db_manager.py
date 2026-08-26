import aiosqlite
from config import DB_PATH

# 1. Barcha suralarni olish
async def get_all_surahs():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM surahs") as cursor:
            return await cursor.fetchall()

# 2. Sura ma'lumotini olish
async def get_surah_info(surah_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM surahs WHERE surah_id = ?", (surah_id,)) as cursor:
            return await cursor.fetchone()

# 3. Oyatni olish
async def get_verse(surah_id: int, verse_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM verses WHERE surah_id = ? AND verse_id = ?", 
            (surah_id, verse_id)
        ) as cursor:
            return await cursor.fetchone()

# 4. Foydalanuvchi joylashuvini saqlash
async def save_user_location(user_id: int, lat: float, lon: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, latitude, longitude) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET latitude = ?, longitude = ?
        """, (user_id, lat, lon, lat, lon))
        await db.commit()

# 5. Foydalanuvchi joylashuvini olish
async def get_user_location(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT latitude, longitude FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

# ==========================================
# 🤲 DUOLAR VA QIDIRUV UCHUN YANGI FUNKSIYALAR
# ==========================================

async def get_all_duas():
    async with aiosqlite.connect(DB_PATH) as db:
        # Agar duolar jadvali yo'q bo'lsa, o'zi avtomat yaratadi va namuna qo'shadi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS duas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                text_arabic TEXT,
                text_translit TEXT,
                text_uzbek TEXT
            )
        """)
        async with db.execute("SELECT COUNT(*) FROM duas") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                # Namuna duolar kiritamiz
                await db.execute("INSERT INTO duas (title, text_arabic, text_translit, text_uzbek) VALUES (?, ?, ?, ?)",
                    ("Rabbano atina", "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ", 
                     "Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan wa qina azaban-nar", 
                     "Rabbimiz! Bizga bu dunyoda ham, oxiratda ham yaxshilik ber va bizni do'zax azobidan saqla.")
                )
                await db.execute("INSERT INTO duas (title, text_arabic, text_translit, text_uzbek) VALUES (?, ?, ?, ?)",
                    ("Qarzdan qutulish duosi", "اللَّهُمَّ اكْفِنِي بِحَلَالِكَ عَنْ حَرَامِكَ، وَأَغْنِنِي بِفَضْلِكَ عَمَّنْ سِوَاكَ", 
                     "Allohummakfini bihalalika an haramika, va ag'nini bifadlika amman sivak", 
                     "Allohim! O'zingning haloling bilan haromingdan kifoya qil va o'z fazling bilan Boshqalarga muhtoj qilib qo'yma.")
                )
                await db.commit()
                
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM duas") as cursor:
            return await cursor.fetchall()

async def get_dua_by_id(dua_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM duas WHERE id = ?", (dua_id,)) as cursor:
            return await cursor.fetchone()

async def search_verses_by_text(keyword: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # O'zbekcha tarjima ichidan kalit so'zni qidiramiz
        async with db.execute(
            "SELECT * FROM verses WHERE text_uzbek LIKE ? LIMIT 10", 
            (f"%{keyword}%",)
        ) as cursor:
            return await cursor.fetchall()
