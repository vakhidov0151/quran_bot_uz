import sqlite3
import requests
import time

print("⏳ Qur'on ma'lumotlari yuklanmoqda... Iltimos kuting (bu 10-15 soniya olishi mumkin).")

try:
    print("📡 Arabcha matnlar olinmoqda...")
    ar_response = requests.get("http://api.alquran.cloud/v1/quran/quran-uthmani").json()
    print("📡 O'zbekcha tarjimalar olinmoqda...")
    uz_response = requests.get("http://api.alquran.cloud/v1/quran/uz.sodik").json()
except Exception as e:
    print(f"❌ Internetga ulanishda xatolik yuz berdi: {e}")
    exit()

ar_surahs = ar_response['data']['surahs']
uz_surahs = uz_response['data']['surahs']

# Bazaga ulanish
conn = sqlite3.connect("data/quran.db")
cursor = conn.cursor()

# Eski (sinov uchun yozilgan) oyatlarni tozalaymiz
cursor.execute("DELETE FROM verses")

verses_data = []
print("⚙️ Ma'lumotlar bazaga tayyorlanmoqda...")

for i in range(114):
    surah_id = ar_surahs[i]['number']
    surah_name_ar = ar_surahs[i]['name']
    surah_name_uz = uz_surahs[i]['englishName'] # Masalan: Al-Baqara
    
    ar_ayahs = ar_surahs[i]['ayahs']
    uz_ayahs = uz_surahs[i]['ayahs']
    
    for j in range(len(ar_ayahs)):
        verse_id = ar_ayahs[j]['numberInSurah']
        text_arabic = ar_ayahs[j]['text']
        text_uzbek = uz_ayahs[j]['text']
        
        # Audio havolalarni avtomatik yasash (Masalan: 002255.mp3)
        audio_id = f"{surah_id:03d}{verse_id:03d}"
        audio_ghamdi = f"https://everyayah.com/data/Ghamadi_40kbps/{audio_id}.mp3"
        audio_hussary = f"https://everyayah.com/data/Husary_64kbps/{audio_id}.mp3"
        
        verses_data.append((
            surah_id, verse_id, surah_name_uz, surah_name_ar, 
            text_arabic, text_uzbek, audio_ghamdi, audio_hussary
        ))

print(f"💾 Jami {len(verses_data)} ta oyat bazaga yozilmoqda...")
cursor.executemany("""
INSERT INTO verses (surah_id, verse_id, surah_name_uz, surah_name_ar, text_arabic, text_uzbek, audio_ghamdi, audio_hussary)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", verses_data)

conn.commit()
conn.close()
print("✅ Barcha 6236 ta oyat bazaga muvaffaqiyatli yuklandi!")