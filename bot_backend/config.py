import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="bot.log",
    filemode="a",
)

aiohttp_logger = logging.getLogger("aiohttp")
aiohttp_logger.setLevel(logging.INFO)


# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_TOKEN = os.getenv("WEATHER_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

if not WEATHER_TOKEN:
    raise ValueError("Переменная окружения WEATHER_TOKEN не установлена!")
