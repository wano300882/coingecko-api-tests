"""
Загрузка конфига из .env файлов.

Переключение окружения через переменную ENV:
    ENV=dev pytest    -> загружает .env.dev
    ENV=prod pytest   -> загружает .env.prod
    pytest            -> по умолчанию dev
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent
_ENV_NAME = os.environ.get("ENV", "dev").lower()
_ENV_FILE = _ROOT / f".env.{_ENV_NAME}"

if not _ENV_FILE.exists():
    raise FileNotFoundError(
        f"Файл окружения не найден: {_ENV_FILE}\n"
        f"Скопируй .env.example в .env.{_ENV_NAME} и заполни значения."
    )

# override=False — если переменная уже есть в shell (например, в CI),
# файл её не перезапишет. Так секреты из GitHub Actions работают правильно.
load_dotenv(_ENV_FILE, override=False)

BASE_URL: str = os.environ.get("BASE_URL", "https://api.coingecko.com/api/v3").rstrip("/")
REQUEST_TIMEOUT: int = int(os.environ.get("REQUEST_TIMEOUT", "10"))
API_KEY: str = os.environ.get("API_KEY", "")

print(f"[config] ENV={_ENV_NAME!r}  BASE_URL={BASE_URL}  TIMEOUT={REQUEST_TIMEOUT}s")
