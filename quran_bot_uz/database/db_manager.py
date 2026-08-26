import aiosqlite
from config import DB_PATH

# Kirillni Lotinga o'giruvchi yordamchi funksiya
def cyrillic_to_latin(text: str) -> str:
    if not text:
        return ""
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
        'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': "'", 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z', 'И': 'I', 'Й': 'Y',
        'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F',
        'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sh', 'Ъ': "'", 'Ы': 'I', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    text = text.replace('ў', "o'").replace('ғ', "g'").replace('қ', "q").replace('ҳ', "h")
    text = text.replace('Ў', "O'").replace('Ғ', "G'").replace('Қ', "Q").replace('Ҳ', "H")
    
    result = []
    for char in text:
        result.append(mapping.get(char, char))
    return "".join(result)


async def get_all_surahs():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM surahs") as cursor:
            rows = await cursor.fetchall()
            # Sura nomlarini ham lotinlashtiramiz
            surahs = []
            for row in rows:
                row_dict = dict(row)
                row_dict['surah_name_uz'] = cyrillic_to_latin(row_dict['surah_name_uz'])
                surahs.append(row_dict)
            return surahs

async def get_surah_info(surah_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM surahs WHERE surah_id = ?", (surah_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                row_dict = dict(row)
                row_dict['surah_name_uz'] = cyrillic_to_latin(row_dict['surah_name_uz'])
                return row_dict
            return None

async def get_verse(surah_id: int, verse_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM verses WHERE surah_id = ? AND verse_id = ?", 
            (surah_id, verse_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                row_dict = dict(row)
                row_dict['text_uzbek'] = cyrillic_to_latin(row_dict['text_uzbek'])
                row_dict['surah_name_uz'] = cyrillic_to_latin(row_dict['surah_name_uz'])
                return row_dict
            return None

async def save_user_location(user_id: int, lat: float, lon: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, latitude, longitude) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET latitude = ?, longitude = ?
        """, (user_id, lat, lon, lat, lon))
        await db.commit()

async def get_user_location(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT latitude, longitude FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def get_all_duas():
    async with aiosqlite.connect(DB_PATH) as db:
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
                await db.execute("INSERT INTO duas (title, text_arabic, text_translit, text_uzbek) VALUES (?, ?, ?, ?)",
                    ("Rabbano atina", "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ", 
                     "Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan wa qina azaban-nar", 
                     "Rabbimiz! Bizga bu dunyoda ham, oxiratda ham yaxshilik ber va bizni do'zax azobidan saqla.")
                )
                await db.commit()
                
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM duas") as cursor:
            rows = await cursor.fetchall()
            duas = []
            for row in rows:
                d = dict(row)
                d['title'] = cyrillic_to_latin(d['title'])
                d['text_uzbek'] = cyrillic_to_latin(d['text_uzbek'])
                duas.append(d)
            return duas

async def get_dua_by_id(dua_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM duas WHERE id = ?", (dua_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                d = dict(row)
                d['title'] = cyrillic_to_latin(d['title'])
                d['text_uzbek'] = cyrillic_to_latin(d['text_uzbek'])
                return d
            return None

async def search_verses_by_text(keyword: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM verses WHERE text_uzbek LIKE ? LIMIT 10", 
            (f"%{keyword}%",)
        ) as cursor:
            rows = await cursor.fetchall()
            verses = []
            for row in rows:
                v = dict(row)
                v['text_uzbek'] = cyrillic_to_latin(v['text_uzbek'])
                v['surah_name_uz'] = cyrillic_to_latin(v['surah_name_uz'])
                verses.append(v)
            return verses
# Foydalanuvchining yozuv turini (latin yoki cyrillic) saqlash
async def set_user_script(user_id: int, script: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET script = ? WHERE user_id = ?
        """, (script, user_id))
        await db.commit()

# Foydalanuvchining tanlagan yozuvini olish (standart 'latin')
async def get_user_script(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT script FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return row[0]
            return 'latin' # Agar tanlamagan bo'lsa standart lotin bo'ladi
