import sqlite3
import os

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/quran.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    surah_id INTEGER,
    verse_id INTEGER,
    surah_name_uz TEXT,
    surah_name_ar TEXT,
    text_arabic TEXT,
    text_uzbek TEXT,
    audio_ghamdi TEXT,
    audio_hussary TEXT
)
""")

sample_data = [
    (
        1, 1, "Fotiha", "الفاتحة",
        "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        "Mehribon va rahmli Allohning nomi ila (boshlayman).",
        "https://everyayah.com/data/Ghamadi_40kbps/001001.mp3",
        "https://everyayah.com/data/Husary_64kbps/001001.mp3"
    ),
    (
        1, 2, "Fotiha", "الفاتحة",
        "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
        "Hamd olamlarning Robbi Allohgadir.",
        "https://everyayah.com/data/Ghamadi_40kbps/001002.mp3",
        "https://everyayah.com/data/Husary_64kbps/001002.mp3"
    ),
    (
        2, 255, "Baqara", "البقرة",
        "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ",
        "Alloh – Undan o‘zga iloh yo‘q. U Tirik va Qayyumdir. Uni mudroq ham, uyqu ham olmas. Osmonlardagi va yerdagi barcha narsa Unikidir...",
        "https://everyayah.com/data/Ghamadi_40kbps/002255.mp3",
        "https://everyayah.com/data/Husary_64kbps/002255.mp3"
    )
]

cursor.executemany("""
INSERT INTO verses (surah_id, verse_id, surah_name_uz, surah_name_ar, text_arabic, text_uzbek, audio_ghamdi, audio_hussary)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", sample_data)

conn.commit()
conn.close()
print("✅ quran.db bazasi muvaffaqiyatli yaratildi!")