import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "data/quran.db"
USER_DB_PATH = "userdata/users.db"

# Admin(lar) ID: Railway Variables'ga ADMIN_IDS=123456789 (bir nechta bo'lsa vergul bilan)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# Namozlar: API kaliti -> (lotincha, kirillcha)
PRAYER_NAMES = {
    "Fajr": ("Bomdod", "Бомдод"),
    "Dhuhr": ("Peshin", "Пешин"),
    "Asr": ("Asr", "Аср"),
    "Maghrib": ("Shom", "Шом"),
    "Isha": ("Xufton", "Хуфтон")
}

# Joylashuv yubora olmaydiganlar uchun (masalan, kompyuterdagi Telegram): viloyat markazlari
# kalit -> (lotincha, kirillcha, kenglik, uzunlik)
CITIES = {
    "toshkent": ("Toshkent", "Тошкент", 41.3111, 69.2797),
    "andijon": ("Andijon", "Андижон", 40.7821, 72.3442),
    "buxoro": ("Buxoro", "Бухоро", 39.7747, 64.4286),
    "fargona": ("Farg'ona", "Фарғона", 40.3864, 71.7864),
    "jizzax": ("Jizzax", "Жиззах", 40.1158, 67.8422),
    "namangan": ("Namangan", "Наманган", 40.9983, 71.6726),
    "navoiy": ("Navoiy", "Навоий", 40.1039, 65.3688),
    "qarshi": ("Qarshi", "Қарши", 38.8606, 65.7891),
    "nukus": ("Nukus", "Нукус", 42.4531, 59.6103),
    "samarqand": ("Samarqand", "Самарқанд", 39.6547, 66.9597),
    "guliston": ("Guliston", "Гулистон", 40.4897, 68.7842),
    "termiz": ("Termiz", "Термиз", 37.2242, 67.2783),
    "urganch": ("Urganch", "Урганч", 41.5500, 60.6333),
}

# Zakot nisobi (so'mda). Tilla narxi o'zgarganda Railway Variables orqali yangilanadi
NISAB_SOM = int(os.getenv("NISAB_SOM", "40000000"))
