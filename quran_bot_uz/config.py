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

# Xatm rejasi: 60 ta hizb (yarim pora) boshlanishi (sura, oyat). Juft indekslar — 30 pora boshlanishi
HIZB_STARTS = [
    (1, 1), (2, 75), (2, 142), (2, 203), (2, 253), (3, 15), (3, 93), (3, 171), (4, 24), (4, 88),
    (4, 148), (5, 27), (5, 82), (6, 36), (6, 111), (7, 1), (7, 88), (7, 171), (8, 41), (9, 34),
    (9, 93), (10, 26), (11, 6), (11, 84), (12, 53), (13, 19), (15, 1), (16, 51), (17, 1), (17, 99),
    (18, 75), (20, 1), (21, 1), (22, 1), (23, 1), (24, 21), (25, 21), (26, 111), (27, 56), (28, 51),
    (29, 46), (31, 22), (33, 31), (34, 24), (36, 28), (37, 145), (39, 32), (40, 41), (41, 47), (43, 24),
    (46, 1), (48, 18), (51, 31), (55, 1), (58, 1), (62, 1), (67, 1), (72, 1), (78, 1), (87, 1),
]
XATM_PLANS = (60, 30, 15, 10)  # necha kunda xatm

# Zakot nisobi (so'mda). Tilla narxi o'zgarganda Railway Variables orqali yangilanadi
NISAB_SOM = int(os.getenv("NISAB_SOM", "40000000"))
