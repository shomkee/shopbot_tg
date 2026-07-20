import os
from dotenv import load_dotenv

load_dotenv()


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ==== Основные настройки ====
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# ID владельца (только он может создавать промокоды)
OWNER_ID = _int(os.getenv("OWNER_ID", "0"))

# Дополнительные админы через запятую: 111,222,333
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x]
if OWNER_ID and OWNER_ID not in ADMIN_IDS:
    ADMIN_IDS.append(OWNER_ID)

# ==== Платёжные системы ====
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "").strip()
CRYPTOBOT_ASSET = os.getenv("CRYPTOBOT_ASSET", "USDT").strip()

XROCKET_TOKEN = os.getenv("XROCKET_TOKEN", "").strip()
XROCKET_ASSET = os.getenv("XROCKET_ASSET", "USDT").strip()

# ==== Магазин ====
# Название магазина — выводится в шапке приветствия и главного меню
SHOP_NAME = os.getenv("SHOP_NAME", "NEON VAULT").strip() or "NEON VAULT"

CURRENCY = os.getenv("CURRENCY", "USDT").strip()
REFERRAL_PERCENT = float(os.getenv("REFERRAL_PERCENT", "5") or 0)

SUPPORT_ACCOUNT = os.getenv("SUPPORT_ACCOUNT", "@support").strip()
RULES = os.getenv(
    "RULES",
    "1. Будьте вежливы с поддержкой.\n"
    "2. Возврат средств не предусмотрен.\n"
    "3. Товар выдаётся автоматически после оплаты.\n"
    "4. Администрация не несёт ответственности за неправильное использование товара.",
)

# Необязательное фото-баннер (file_id или прямая ссылка на картинку).
# Если задано — все inline-меню будут приходить как фото с кнопками.
BANNER_PHOTO = os.getenv("BANNER_PHOTO", "").strip()

DB_PATH = os.getenv("DB_PATH", "shop.db").strip()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID
