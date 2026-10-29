import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "data/quran.db"
USER_DB_PATH = "userdata/users.db"

# Admin(lar) ID: Railway Variables'ga ADMIN_IDS=123456789 (bir nechta bo'lsa vergul bilan)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

# Zakot nisobi (so'mda). Tilla narxi o'zgarganda Railway Variables orqali yangilanadi
NISAB_SOM = int(os.getenv("NISAB_SOM", "40000000"))
