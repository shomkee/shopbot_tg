import html

from aiogram.types import CallbackQuery, Message

from config import BANNER_PHOTO

# ── Дизайн-система бота ─────────────────────────────────────
# Фирменный стиль: тонкие маркеры вместо стандартных эмодзи
#   ⟡ витрина/товар   ⌁ деньги   ⌘ кабинет   ✦ рефералы
#   ✆ поддержка       ⚿ промокод ▲ админка   ✓ / ✕ статусы
# LINE — фирменная линейка-разделитель под заголовком экрана.
LINE = "━" * 15


def esc(text) -> str:
    return html.escape(str(text)) if text is not None else ""


async def send_menu(event, text, keyboard=None, photo=None):
    """Универсальная отправка меню.

    Если задано фото (BANNER_PHOTO или фото товара) — отправляет фото с подписью
    и inline-кнопками (пункт ТЗ 11). Иначе — обычный текст.
    Для CallbackQuery предыдущее сообщение удаляется, чтобы не плодить меню.
    """
    photo = photo or BANNER_PHOTO or None

    if isinstance(event, CallbackQuery):
        try:
            await event.message.delete()
        except Exception:
            pass
        target = event.message
    else:
        target = event

    if photo:
        try:
            await target.answer_photo(photo=photo, caption=text, reply_markup=keyboard)
            return
        except Exception:
            # если file_id/ссылка недоступны — откатываемся на текст
            pass
    await target.answer(text, reply_markup=keyboard)
