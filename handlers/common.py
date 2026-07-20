from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from config import RULES, SHOP_NAME, SUPPORT_ACCOUNT, is_admin
from database import get_or_create_user
from keyboards import back_kb, main_inline_kb, main_menu_kb, support_kb
from utils import LINE, esc, send_menu

router = Router()

WELCOME = (
    f"⟢ <b>{esc(SHOP_NAME)}</b>\n"
    "<i>цифровые товары · моментальная выдача</i>\n"
    f"{LINE}\n"
    "▸ товар приходит сразу после оплаты\n"
    "▸ оплата криптой — xRocket / CryptoBot\n"
    "▸ бонусы за друзей и промокоды\n\n"
    "<i>выбирай раздел на клавиатуре ↓</i>"
)

MENU_TEXT = (
    f"⟢ <b>{esc(SHOP_NAME)}</b>\n"
    f"{LINE}\n"
    "<i>главное меню — куда дальше?</i>"
)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    referrer_id = None
    if command.args and command.args.strip().isdigit():
        referrer_id = int(command.args.strip())
    await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        referrer_id,
    )
    await message.answer(
        WELCOME, reply_markup=main_menu_kb(is_admin(message.from_user.id))
    )
    await send_menu(message, MENU_TEXT, main_inline_kb())


@router.callback_query(F.data == "menu")
async def cb_menu(cb: CallbackQuery):
    await send_menu(cb, MENU_TEXT, main_inline_kb())
    await cb.answer()


# ===== ПОДДЕРЖКА (пункт ТЗ 8) =====
def _support_text():
    return (
        f"✆ <b>Поддержка</b>\n{LINE}\n"
        f"на связи живой человек: {esc(SUPPORT_ACCOUNT)}\n"
        "поможем с оплатой, выдачей и любым вопросом\n\n"
        "<i>перед обращением загляни в правила ↓</i>"
    )


@router.message(F.text == "✆ Поддержка")
async def support_msg(message: Message):
    await send_menu(message, _support_text(), support_kb())


@router.callback_query(F.data == "support")
async def support_cb(cb: CallbackQuery):
    await send_menu(cb, _support_text(), support_kb())
    await cb.answer()


@router.callback_query(F.data == "rules")
async def rules_cb(cb: CallbackQuery):
    await send_menu(
        cb, f"§ <b>Правила</b>\n{LINE}\n{esc(RULES)}", back_kb("support")
    )
    await cb.answer()
