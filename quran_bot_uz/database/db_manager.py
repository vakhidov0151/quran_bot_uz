import aiosqlite
import datetime
from zoneinfo import ZoneInfo
from config import DB_PATH, USER_DB_PATH

def cyrillic_to_latin(text: str) -> str:
    if not text: return ""
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
    result = [mapping.get(char, char) for char in text]
    return "".join(result)

def latin_to_cyrillic(text: str) -> str:
    if not text: return ""
    mapping = {
        'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 'j': 'ж', 'z': 'з', 'i': 'и', 'y': 'й',
        'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у', 'f': 'ф',
        'x': 'х', 'q': 'қ', 'h': 'ҳ'
    }
    text = text.lower()
    text = text.replace("o'", "ў").replace("g'", "ғ").replace("sh", "ш").replace("ch", "ч").replace("ts", "ц")
    result = [mapping.get(char, char) for char in text]
    return "".join(result)

async def ensure_user(user_id: int):
    async with aiosqlite.connect(USER_DB_PATH) as db:
        try:
            await db.execute("ALTER TABLE users ADD COLUMN script TEXT DEFAULT 'latin'")
            await db.commit()
        except: pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN qari TEXT DEFAULT 'alafasy'")
            await db.commit()
        except: pass
        
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if not await cursor.fetchone():
                await db.execute("INSERT INTO users (user_id, script, qari) VALUES (?, 'latin', 'alafasy')", (user_id,))
                await db.commit()

async def set_user_script(user_id: int, script: str):
    await ensure_user(user_id)
    async with aiosqlite.connect(USER_DB_PATH) as db:
        await db.execute("UPDATE users SET script = ? WHERE user_id = ?", (script, user_id))
        await db.commit()

async def get_user_script(user_id: int) -> str:
    try:
        async with aiosqlite.connect(USER_DB_PATH) as db:
            async with db.execute("SELECT script FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]: return row[0]
    except: pass
    return 'latin'

async def get_users_count() -> int:
    try:
        async with aiosqlite.connect(USER_DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    except:
        return 0

async def set_user_qari(user_id: int, qari: str):
    await ensure_user(user_id)
    async with aiosqlite.connect(USER_DB_PATH) as db:
        await db.execute("UPDATE users SET qari = ? WHERE user_id = ?", (qari, user_id))
        await db.commit()

async def get_user_qari(user_id: int) -> str:
    try:
        async with aiosqlite.connect(USER_DB_PATH) as db:
            async with db.execute("SELECT qari FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]: return row[0]
    except: pass
    return 'alafasy'

def translate_dict(d: dict, script: str):
    if script == 'cyrillic': return d
    for k, v in d.items():
        if isinstance(v, str) and not v.startswith('http') and not any('\u0600' <= c <= '\u06FF' for c in v):
            d[k] = cyrillic_to_latin(v)
    return d

async def get_all_surahs(script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT DISTINCT surah_id, surah_name_uz, surah_name_ar FROM verses ORDER BY surah_id"
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [translate_dict(dict(row), script) for row in rows]

async def get_surah_info(surah_id: int, script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT surah_id, surah_name_uz, surah_name_ar, COUNT(verse_id) as total_verses FROM verses WHERE surah_id = ? GROUP BY surah_id"
        async with db.execute(query, (surah_id,)) as cursor:
            row = await cursor.fetchone()
            return translate_dict(dict(row), script) if row else None

async def get_verse(surah_id: int, verse_id: int, script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM verses WHERE surah_id = ? AND verse_id = ?", (surah_id, verse_id)) as cursor:
            row = await cursor.fetchone()
            return translate_dict(dict(row), script) if row else None

# === YANGI FUNKSIYA: SURA NOMI VA OYAT RAQAMI BO'YICHA QIDIRISH ===
async def get_verse_by_sura_name(keyword: str, verse_id: int, script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        search_word1 = f"%{latin_to_cyrillic(keyword)}%"
        search_word2 = f"%{keyword}%"
        # Ikkala yozuvda ham izlaymiz (name_uz yoki surah_name_uz)
        query = """
            SELECT * FROM verses 
            WHERE (surah_name_uz LIKE ? OR surah_name_uz LIKE ? OR name_uz LIKE ? OR name_uz LIKE ?) 
            AND verse_id = ? LIMIT 1
        """
        async with db.execute(query, (search_word1, search_word2, search_word1, search_word2, verse_id)) as cursor:
            row = await cursor.fetchone()
            return translate_dict(dict(row), script) if row else None

async def save_user_location(user_id: int, latitude: float, longitude: float):
    await ensure_user(user_id)
    async with aiosqlite.connect(USER_DB_PATH) as db:
        await db.execute(
            "UPDATE users SET latitude = ?, longitude = ? WHERE user_id = ?",
            (latitude, longitude, user_id)
        )
        await db.commit()

async def get_user_location(user_id: int):
    try:
        async with aiosqlite.connect(USER_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT latitude, longitude FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row and row['latitude'] else None
    except:
        return None

async def get_all_users_locations():
    try:
        async with aiosqlite.connect(USER_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, latitude, longitude FROM users WHERE latitude IS NOT NULL") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
    except Exception as e:
        print(f"Baza xatosi: {e}")
        return []

async def get_all_duas(script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS duas (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, text_arabic TEXT, text_translit TEXT, text_uzbek TEXT)")
        
        count = 0
        async with db.execute("SELECT COUNT(*) FROM duas") as cursor:
            count = (await cursor.fetchone())[0]
            
        if count < 10:
            await db.execute("DROP TABLE duas")
            await db.execute("CREATE TABLE duas (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, text_arabic TEXT, text_translit TEXT, text_uzbek TEXT)")
            duas_data = [
                ("Раббана атина", "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ", "Раббана атина фид-дуня ҳасанатан ва фил-ахироти ҳасанатан ва қина азабан-нар.", "Парвардигоро, бизга бу дунёда ҳам, охиратда ҳам яхшиликни бергин ва бизни дўзах олови азобидан сақлагин."),
                ("Илм сўраш дуоси", "رَبِّ زِدْنِي عِلْمًا", "Робби зидни илман.", "Парвардигорим, илмимни зиёда қилгин."),
                ("Ота-она ҳаққига дуо", "رَّبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا", "Роббирҳамҳума кама роббаяни соғийро.", "Парвардигорим, мени гўдаклик чоғимда тарбиялаганларидек, Сен ҳам уларга раҳм қилгин."),
                ("Қалбни ҳидоятда тутиш", "رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا وَهَبْ لَنَا مِن لَّدُنكَ رَحْمَةً ۚ إِنَّكَ أَنتَ الْوَهَّابُ", "Роббана ла тузиғ қулубана баъда из ҳадайтана ва ҳаб лана мин ладунка роҳматан, иннака антал-ваҳҳаб.", "Парвардигоро, бизни ҳидоят қилганингдан кейин дилларимизни ҳақ йўлдан оғдирма ва бизга Ўз ҳузурингдин раҳмат ато эт. Албатта, Сен барча неъматларни ато этгувчисан."),
                ("Ғам-ташвишдан паноҳ сўраш", "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ", "Аллоҳумма инни аъузу бика минал ҳамми вал ҳазан.", "Ё Аллоҳ, мен Сендан ғам ва қайғудан паноҳ сўрайман."),
                ("Қарздан қутулиш дуоси", "اللَّهُمَّ اكْفِنِي بِحَلَالِكَ عَنْ حَرَامِكَ وَأَغْنِنِي بِفَضْلِكَ عَمَّنْ سِوَاكَ", "Аллоҳуммакфини биҳалалика ъан ҳаромика ва ағнини бифазлика ъамман сивака.", "Ё Аллоҳ, менга ҳалолинг билан ҳаромингдан кифоя қилгин ва Ўз фазлинг билан мени Ўзингдан бошқалардан беҳожат қилгин."),
                ("Шифо сўраш дуоси", "أَنِّي مَسَّنِيَ الضُّرُّ وَأَنتَ أَرْحَمُ الرَّاحِمِينَ", "Анни массанияд-дурру ва анта арҳамур-роҳимийн.", "(Парвардигорим), Албатта, менга бало етди. Сен раҳмлиларнинг раҳмлироғисан."),
                ("Истиғфор (Юнус а.с. дуоси)", "لَّا إِلَهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ", "Ла илаҳа илла анта субҳанака инни кунту миназ-золимийн.", "Сендан ўзга илоҳ йўқ. Сен поксан. Албатта, мен золимлардан бўлдим."),
                ("Уйга киришда ўқиладиган дуо", "بِسْمِ اللَّهِ وَلَجْنَا، وَبِسْمِ اللَّهِ خَرَجْنَا، وَعَلَى رَبِّنَا تَوَكَّلْنَا", "Бисмиллаҳи валажна, ва бисмиллаҳи харожна, ва ъала Роббина таваккална.", "Аллоҳнинг номи билан кирдик ва Аллоҳнинг номи билан чиқдик ҳамда Роббимизга таваккал қилдик."),
                ("Сафар дуоси", "سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ وَإِنَّا إِلَى رَبِّنَا لَمُنقَلِبُونَ", "Субҳаналлази саххоро лана ҳаза ва ма кунна лаҳу муқринийн, ва инна ила Роббина ламунқолибун.", "Бизга буни бўйсундириб қўйган Зот покдир. Биз бунга қодир эмас эдик. Ва албатта биз Роббимизга қайтгувчилармиз.")
            ]
            await db.executemany("INSERT INTO duas (title, text_arabic, text_translit, text_uzbek) VALUES (?, ?, ?, ?)", duas_data)
            await db.commit()
            
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM duas") as cursor:
            rows = await cursor.fetchall()
            return [translate_dict(dict(row), script) for row in rows]

async def get_dua_by_id(dua_id: int, script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM duas WHERE id = ?", (dua_id,)) as cursor:
            row = await cursor.fetchone()
            return translate_dict(dict(row), script) if row else None

async def search_verses_by_text(keyword: str, script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        search_word = latin_to_cyrillic(keyword) if script == 'latin' else keyword
        async with db.execute("SELECT * FROM verses WHERE text_uzbek LIKE ? LIMIT 10", (f"%{search_word}%",)) as cursor:
            rows = await cursor.fetchall()
            return [translate_dict(dict(row), script) for row in rows]

CUSTOM_VERSES = [
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
    (2, 104), (2, 138), (2, 153), (2, 172), (2, 183), (2, 208), (2, 254), (2, 255), (2, 264), (2, 267), (2, 278), (2, 282),
    (3, 2), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 100), (3, 102), (3, 118), (3, 130), (3, 149), (3, 200),
    (4, 29), (4, 59), (4, 133), (4, 135), (4, 136), (4, 144),
    (5, 1), (24, 31),
    (55, 19), (55, 27), (55, 29), (55, 33), (55, 37), (55, 46), (55, 60)
]

async def get_random_verse(script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.datetime.now(ZoneInfo("Asia/Tashkent"))
        
        if now.weekday() == 4:
            # Juma kuni uchun Maxsus: Juma surasi, 9-10 oyatlar
            async with db.execute("SELECT * FROM verses WHERE surah_id = 62 AND verse_id IN (9, 10) ORDER BY verse_id") as cursor:
                rows = await cursor.fetchall()
                if rows and len(rows) == 2:
                    row1 = dict(rows[0])
                    row2 = dict(rows[1])
                    
                    combined = row1.copy()
                    combined['verse_id'] = "9-10"
                    
                    ar_col = 'text_arabic' if 'text_arabic' in row1 else 'arabic'
                    uz_col = 'text_uzbek' if 'text_uzbek' in row1 else 'uzbek' if 'uzbek' in row1 else 'text'
                    
                    combined[ar_col] = row1.get(ar_col, '') + " ۝ " + row2.get(ar_col, '')
                    combined[uz_col] = row1.get(uz_col, '') + " " + row2.get(uz_col, '')
                    
                    return translate_dict(combined, script)
                    
        day_index = now.toordinal() % len(CUSTOM_VERSES)
        sura_id, ayah_id = CUSTOM_VERSES[day_index]
        async with db.execute("SELECT * FROM verses WHERE surah_id = ? AND verse_id = ?", (sura_id, ayah_id)) as cursor:
            row = await cursor.fetchone()
            return translate_dict(dict(row), script) if row else None

async def get_all_asmaulhusna(script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS asma (id INTEGER PRIMARY KEY, arabic TEXT, latin TEXT, uzbek TEXT)")
        
        # Cursor'ni yopib keyin drop qilish uchun
        count = 0
        async with db.execute("SELECT COUNT(*) FROM asma") as cursor:
            count = (await cursor.fetchone())[0]
            
        if count < 99:
            await db.execute("DROP TABLE asma")
            await db.execute("CREATE TABLE asma (id INTEGER PRIMARY KEY, arabic TEXT, latin TEXT, uzbek TEXT)")
            asma_data = [
                    (1, "الرَّحْمَنُ", "Ar-Rahmon", "Mehribon — Barcha maxluqotlarga rahmat qiluvchi."),
                    (2, "الرَّحِيمُ", "Ar-Rohiym", "Rahmli — Oxiratda faqat mo'minlarga rahmat qiluvchi."),
                    (3, "الْمَلِكُ", "Al-Malik", "Podshoh — Barcha narsaning egasi va haqiqiy hukmdori."),
                    (4, "الْقُدُّوسُ", "Al-Quddus", "Muqaddas — Barcha ayb va nuqsonlardan pok zot."),
                    (5, "السَّلَامُ", "As-Salom", "Omonlik beruvchi — Barcha ofatlardan salomat saqlovchi."),
                    (6, "الْمُؤْمِنُ", "Al-Mo'min", "Iymon va omonlik beruvchi."),
                    (7, "الْمُهَيْمِنُ", "Al-Muhaymin", "Kuzatib turuvchi — Hamma narsani asrab, himoya qiluvchi."),
                    (8, "الْعَزِيزُ", "Al-Aziz", "Izzatli — Barcha narsadan g'olib va qudratli."),
                    (9, "الْجَبَّارُ", "Al-Jabbor", "Nuqsonlarni tuzatuvchi, xohishiga bo'ysundiruvchi."),
                    (10, "الْمُتَكَبِّرُ", "Al-Mutakabbir", "Ulug'vor — Kibr va ulug'lik faqat unga xos zot."),
                    (11, "الْخَالِقُ", "Al-Xoliq", "Yaratuvchi — Barcha narsani yo'qdan bor qiluvchi."),
                    (12, "الْبَارِئُ", "Al-Bari'", "Yo'qdan paydo qiluvchi."),
                    (13, "الْمُصَوِّرُ", "Al-Musovvir", "Maxluqotlarga suvrat va shakl beruvchi."),
                    (14, "الْغَفَّارُ", "Al-G'offor", "Bandalarning xatolarini ko'plab kechiruvchi."),
                    (15, "الْقَهَّارُ", "Al-Qohhor", "Barcha maxluqotlarni o'z hukmiga bo'ysundiruvchi."),
                    (16, "الْوَهَّابُ", "Al-Vahhob", "Ne'matlarni ne'mat qilib, behisob beruvchi."),
                    (17, "الرَّزَّاقُ", "Ar-Razzoq", "Barcha maxluqotlarning rizqini yetkazib beruvchi."),
                    (18, "الْفَتَّاحُ", "Al-Fattoh", "Barcha mushkullarni ochuvchi, yengillik beruvchi."),
                    (19, "الْعَلِيمُ", "Al-Aliym", "Barcha narsani o'ta aniqlik bilan biluvchi."),
                    (20, "الْقَابِضُ", "Al-Qobiz", "Xohlagan bandasining rizqini tor qiluvchi."),
                    (21, "الْبَاسِطُ", "Al-Bosit", "Xohlagan bandasining rizqini keng qiluvchi."),
                    (22, "الْخَافِضُ", "Al-Xofiz", "Kofir va zolimlarning martabasini pasaytiruvchi."),
                    (23, "الرَّافِعُ", "Ar-Rofe'", "Mo'minlarning darajasini ko'taruvchi."),
                    (24, "الْمُعِزُّ", "Al-Mu'izz", "Xohlagan bandasini aziz qiluvchi."),
                    (25, "الْمُذِلُّ", "Al-Muzill", "Xohlagan bandasini xor qiluvchi."),
                    (26, "السَّمِيعُ", "As-Samiy'", "Barcha narsani eshituvchi."),
                    (27, "الْبَصِيرُ", "Al-Basiyr", "Barcha narsani ko'ruvchi."),
                    (28, "الْحَكَمُ", "Al-Hakam", "Adolat bilan hukm qiluvchi."),
                    (29, "الْعَدْلُ", "Al-Adl", "Mutlaq adolat qiluvchi zot."),
                    (30, "اللَّطِيفُ", "Al-Latiyf", "O'ta lutfli, sirlarni biluvchi."),
                    (31, "الْخَبِيرُ", "Al-Xobiyr", "Hamma narsadan xabardor."),
                    (32, "الْحَلِيمُ", "Al-Haliym", "Jazo berishga shoshmaydigan, hilm egasi."),
                    (33, "الْعَظِيمُ", "Al-Aziym", "O'ta ulug' va azamatli zot."),
                    (34, "الْغَفُورُ", "Al-G'ofur", "Ko'p mag'firat qiluvchi, kechiruvchi."),
                    (35, "الشَّكُورُ", "Ash-Shakur", "Oz amalga ko'p savob beruvchi."),
                    (36, "الْعَلِيُّ", "Al-Aliy", "Martabasi oliy va yuksak."),
                    (37, "الْكَبِيرُ", "Al-Kabiyr", "Zoti va qadr-qimmati ulug' zot."),
                    (38, "الْحَفِيظُ", "Al-Hafiyz", "Barcha narsani o'z panohida saqlovchi."),
                    (39, "الْمُقِيتُ", "Al-Muqiyt", "Barcha maxluqotlarga rizq va quvvat beruvchi."),
                    (40, "الْحَسِيبُ", "Al-Hasiyb", "Kifoya qiluvchi, qiyomatda hisob-kitob qiluvchi."),
                    (41, "الْجَلِيلُ", "Al-Jaliyl", "Sifatlarida ulug'lik egasi."),
                    (42, "الْكَرِيمُ", "Al-Kariym", "O'ta saxovatli, karamli zot."),
                    (43, "الرَّقِيبُ", "Ar-Roqiyb", "Barcha narsani kuzatib, nazorat qilib turuvchi."),
                    (44, "الْمُجِيبُ", "Al-Mujiyb", "Duolarni ijobat qiluvchi, qabul qiluvchi."),
                    (45, "الْوَاسِعُ", "Al-Vose'", "Ilmi va rahmati barcha narsani qamrab olgan."),
                    (46, "الْحَكِيمُ", "Al-Hakiym", "Hikmat sohibi, har bir ishni hikmat bilan qiluvchi."),
                    (47, "الْوَدُودُ", "Al-Vadud", "Bandalarni yaxshi ko'ruvchi va sevimli zot."),
                    (48, "الْمَجِيدُ", "Al-Majiyd", "Shon-sharafi, qadri ulug' zot."),
                    (49, "الْبَاعِثُ", "Al-Bo'is", "O'liklarni tiriltiruvchi, payg'ambarlar yuboruvchi."),
                    (50, "الشَّهِيدُ", "Ash-Shahiyd", "Barcha narsaga guvoh bo'lib turuvchi."),
                    (51, "الْحَقُّ", "Al-Haq", "Haqiqatdan mavjud, o'zgarmas zot."),
                    (52, "الْوَكِيلُ", "Al-Vakiyl", "Barcha ishlarni o'ziga topshiriladigan vakil."),
                    (53, "الْقَوِيُّ", "Al-Qoviy", "Haqiqiy quvvat va kuch egasi."),
                    (54, "الْمَتِينُ", "Al-Matiyn", "Juda qudratli, hech qachon zaiflashmaydigan."),
                    (55, "الْوَلِيُّ", "Al-Valiy", "Mo'minlarning do'sti, yordamchisi."),
                    (56, "الْحَمِيدُ", "Al-Hamiyd", "Barcha maqtovlarga munosib va loyiq."),
                    (57, "الْمُحْصِي", "Al-Muhsiy", "Barcha narsaning soni va hisobini biluvchi."),
                    (58, "الْمُبْدِئُ", "Al-Mubdi'", "Barcha narsani yo'qdan bor qilib boshlovchi."),
                    (59, "الْمُعِيدُ", "Al-Mu'iyd", "Yaratilganlarni yana o'z holiga qaytaruvchi (o'ldirib, tiriltiruvchi)."),
                    (60, "الْمُحْيِي", "Al-Muhyi", "Tiriltiruvchi, hayot baxsh etuvchi."),
                    (61, "الْمُمِيتُ", "Al-Mumiyt", "O'ldiruvchi, jonni oluvchi."),
                    (62, "الْحَيُّ", "Al-Hayy", "Doim tirik, o'lmaydigan barhayot zot."),
                    (63, "الْقَيُّومُ", "Al-Qoyyum", "O'z-o'zidan qoim turuvchi, barchani ushlab turuvchi."),
                    (64, "الْوَاجِدُ", "Al-Vojid", "Barcha narsani topuvchi, hech narsaga muhtoj emas."),
                    (65, "الْمَاجِدُ", "Al-Mojid", "Ulug'lik va sharaf egasi."),
                    (66, "الْوَاحِدُ", "Al-Vohid", "Yakka, yagona zot."),
                    (67, "الْأَحَد", "Al-Ahad", "Hech qanday sherigi va o'xshashi yo'q."),
                    (68, "الصَّمَدُ", "As-Somad", "Barchaning hojati unga tushadigan, o'zi behojat zot."),
                    (69, "الْقَادِرُ", "Al-Qodir", "Barcha narsaga qodir."),
                    (70, "الْمُقْتَدِرُ", "Al-Muqtadir", "O'ta qudratli, qudratini namoyon qiluvchi."),
                    (71, "الْمُقَدِّمُ", "Al-Muqoddim", "Olg'a suruvchi, xohlaganini oldinga o'tkazuvchi."),
                    (72, "الْمُؤَخِّرُ", "Al-Muaxxir", "Ortga suruvchi, xohlaganini orqaga qoldiruvchi."),
                    (73, "الْأَوَّلُ", "Al-Avval", "Hamma narsadan avval bor bo'lgan, boshlanishi yo'q."),
                    (74, "الْآخِرُ", "Al-Axir", "Hamma narsa yo'q bo'lganda ham qoluvchi, oxiri yo'q."),
                    (75, "الظَّاهِرُ", "Az-Zohir", "Mavjudligi va qudrati ochiq-oydin ko'rinib turuvchi."),
                    (76, "الْبَاطِنُ", "Al-Botin", "Zoti ko'zdan maxfiy, lekin hamma narsaning botinini biluvchi."),
                    (77, "الْوَالِي", "Al-Voliy", "Barcha ishlarni va maxluqotlarni boshqaruvchi."),
                    (78, "الْمُتَعَالِي", "Al-Muta'ol", "Yaratilganlarning barcha nuqsonli sifatlaridan oliy."),
                    (79, "الْبَرُّ", "Al-Barr", "Keng yaxshilik qiluvchi, mehribon."),
                    (80, "التَّوَّابُ", "At-Tavvob", "Bandalarning tavbalarini ko'plab qabul qiluvchi."),
                    (81, "الْمُنْتَقِمُ", "Al-Muntaqim", "Zolimlardan va osiylardan intiqom oluvchi."),
                    (82, "الْعَفُوُّ", "Al-Afuvv", "Gunohlarni kechiruvchi, o'chirib yuboruvchi."),
                    (83, "الرَّءُوفُ", "Ar-Ra'uf", "O'ta mehribon va shafqatli."),
                    (84, "مَالِكُ الْمُلْكِ", "Molikul-Mulk", "Barcha mulkning yagona va mutlaq egasi."),
                    (85, "ذُو الْجَلَالِ وَالْإِكْرَامِ", "Zul-Jaloli val-Ikrom", "Ulug'lik, sharaf va ikrom egasi."),
                    (86, "الْمُقْسِطُ", "Al-Muqsit", "O'ta adolatli zot."),
                    (87, "الْجَامِعُ", "Al-Jome'", "Qiyomat kuni barchani bir joyga jamlovchi."),
                    (88, "الْغَنِيُّ", "Al-G'oniy", "Hamma unga muhtoj, O'zi hech kimga muhtoj bo'lmagan boy."),
                    (89, "الْمُغْنِي", "Al-Mug'niy", "Xohlagan bandasini boy va behojat qiluvchi."),
                    (90, "الْمَانِعُ", "Al-Mone'", "Man qiluvchi, yomonliklarni to'suvchi."),
                    (91, "الضَّارُّ", "Ad-Dorr", "Xohlaganiga zarar yetkazuvchi."),
                    (92, "النَّافِعُ", "An-Nofe'", "Xohlaganiga manfaat va foyda beruvchi."),
                    (93, "النُّورُ", "An-Nur", "O'z zoti va barcha maxluqotlarini nurlantiruvchi."),
                    (94, "الْهَادِي", "Al-Hadiy", "To'g'ri yo'lga, hidoyatga boshlovchi."),
                    (95, "الْبَدِيعُ", "Al-Badiy'", "O'xshashi va misoli yo'q narsalarni yaratuvchi."),
                    (96, "الْبَاقِي", "Al-Boqiy", "Doimiy qoluvchi, foniylikdan yiroq zot."),
                    (97, "الْوَارِثُ", "Al-Voris", "Barcha narsa foniydir, barcha narsa Unga meros bo'lib qoladi."),
                    (98, "الرَّشِيدُ", "Ar-Rashiyd", "Barcha ishlarni to'g'ri va hikmat bilan boshqaruvchi."),
                    (99, "الصَّبُورُ", "As-Sabur", "Gunohkorlarga jazo berishga shoshilmaydigan, o'ta sabrli.")
                ]
                await db.executemany("INSERT INTO asma (id, arabic, latin, uzbek) VALUES (?, ?, ?, ?)", asma_data)
                await db.commit()
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM asma ORDER BY id") as cursor:
            rows = await cursor.fetchall()
            return [translate_dict(dict(row), script) for row in rows]

async def get_asma_by_id(asma_id: int, script='latin'):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM asma WHERE id = ?", (asma_id,)) as cursor:
            row = await cursor.fetchone()
            return translate_dict(dict(row), script) if row else None
