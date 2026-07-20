from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from config import is_admin
from database import get_user


class BlockMiddleware(BaseMiddleware):
    """Не пропускает заблокированных пользователей (пункт ТЗ 7)."""

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user and not is_admin(user.id):
            db_user = await get_user(user.id)
            if db_user and db_user["is_blocked"]:
                if isinstance(event, CallbackQuery):
                    await event.answer("✕ Доступ закрыт.", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer("✕ Доступ к боту закрыт администрацией.")
                return
        return await handler(event, data)
