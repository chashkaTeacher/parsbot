# config.py
import os

# Токен бота (замените на свой)
BOT_TOKEN = "7716506261:AAEhZS5k-0OaEsIyZdYYJcQq2JPAK01TONM"

# Базовая папка для JSON-файлов с заданиями
JSON_DIR = os.path.join(os.getcwd(), "tasks_json")

# Папка для изображений (можно использовать абсолютный или относительный путь)
IMAGES_DIR = os.path.join(os.getcwd(), "images")

# Таймауты (в секундах)
PAGE_LOAD_TIMEOUT = 5
TASKS_LOAD_TIMEOUT = 10
