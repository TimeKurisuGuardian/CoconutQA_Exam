import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env в окружение системы
load_dotenv()

class SuperAdminCreds:
    USERNAME = os.getenv('SUPER_ADMIN_USERNAME')
    PASSWORD = os.getenv('SUPER_ADMIN_PASSWORD')