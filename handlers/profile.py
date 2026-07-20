from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from config import CURRENCY, REFERRAL_PERCENT
from database import (
    count_referrals,
    add_balance,
    get_purchase,
    get_purchases,
    get_user,
    use_promo,
)
from keyboards import back_kb, history_kb, profile_kb
from utils import LINE, esc, send_menu

router = Router()

PAGE_SIZE = 5


class PromoState(StatesGroup):
    code = State()


async def _profile_text(user_id):
    u = await get_user(user_id)
    refs = await count_referrals(user_id)
    return (
        f"⌘ <b>Кабинет</b>\n{LINE}\n"
        f"id · <code>{user_id}</code>\n"
        f"баланс · <b>{round(u['balance'], 2)} {CURRENCY}</b>\n"
        f"покупок на · {round(u['total_spent'], 2)} {CURRENCY}\n"
        f"пополнено · {round(u['total_deposited'], 2)} {CURRENCY}\n"
        f"{LINE}\n"
        f"✦ друзей приведено · <b>{refs}</b>\n"
        f"✦ бонусов с них · <b>{round(u['referral_earned'], 2)} {CURRENCY}</b>"
    )


@router.message(F.text == "⌘ Кабинет")
async def profile_msg(message: Message):
    await send_menu(message, await _profile_text(message.from_user.id), profile_kb())


@router.callback_query(F.data == "profile")
async def profile_cb(cb: CallbackQuery):
    await send_menu(cb, await _profile_text(cb.from_user.id), profile_kb())
    await cb.answer()


# ===== ИСТОРИЯ ПОКУПОК (пункт ТЗ 4) =====
@router.callback_query(F.data.startswith("history:"))
async def history_cb(cb: CallbackQuery):
    page = int(cb.data.split(":")[1])
    purchases = await get_purchases(cb.from_user.id)
    if not purchases:
        await send_menu(
            cb,
            f"≡ <b>Покупки</b>\n{LINE}\nздесь пока пусто — самое время что-нибудь присмотреть ⟡",
            back_kb("profile"),
        )
        await cb.answer()
        return
    total_pages = (len(purchases) + PAGE_SIZE - 1) // PAGE_SIZE
    page = max(0, min(page, total_pages - 1))
    chunk = purchases[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

    lines = [f"≡ <b>Покупки</b>\n{LINE}"]
    for p in chunk:
        lines.append(
            f"#{p['id']} · {esc(p['product_name'])} · {p['price']} {CURRENCY}"
        )
    lines.append(f"\n— страница {page + 1}/{total_pages} —")
    lines.append("<i>жми на покупку — пришлю файлом ⇩</i>")

    await send_menu(cb, "\n".join(lines), history_kb(chunk, page, total_pages))
    await cb.answer()


@router.callback_query(F.data.startswith("export:"))
async def export_purchase(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    p = await get_purchase(pid)
    if not p or p["user_id"] != cb.from_user.id:
        await cb.answer("Покупка не найдена", show_alert=True)
        return
    content = (
        f"Товар: {p['product_name']}\n"
        f"Цена: {p['price']} {CURRENCY}\n"
        f"Номер покупки: {p['id']}\n"
        f"{'-' * 30}\n"
        f"{p['content']}\n"
    )
    file = BufferedInputFile(content.encode("utf-8"), filename=f"purchase_{pid}.txt")
    await cb.message.answer_document(
        file, caption=f"⇩ покупка #{pid} · {esc(p['product_name'])}"
    )
    await cb.answer("Файл улетел ⇩")


# ===== РЕФЕРАЛЬНАЯ СИСТЕМА (пункт ТЗ 5) =====
@router.callback_query(F.data == "ref")
async def referral_cb(cb: CallbackQuery, bot: Bot):
    me = await bot.me()
    link = "https://t.me/" + me.username + "?start=" + str(cb.from_user.id)
    refs = await count_referrals(cb.from_user.id)
    u = await get_user(cb.from_user.id)
    text = (
        f"✦ <b>Рефералы</b>\n{LINE}\n"
        f"зови друзей — получай <b>{REFERRAL_PERCENT}%</b>\n"
        "с каждого их пополнения, навсегда\n\n"
        f"приглашено · <b>{refs}</b>\n"
        f"заработано · <b>{round(u['referral_earned'], 2)} {CURRENCY}</b>\n\n"
        "твоя личная ссылка:\n"
        f"<code>{link}</code>"
    )
    await send_menu(cb, text, back_kb("profile"))
    await cb.answer()


# ===== АКТИВАЦИЯ ПРОМОКОДА (пункт ТЗ 6) =====
@router.callback_query(F.data == "promo")
async def promo_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(PromoState.code)
    await send_menu(
        cb,
        f"⚿ <b>Промокод</b>\n{LINE}\nвведи код одним сообщением:",
        back_kb("profile"),
    )
    await cb.answer()


@router.message(PromoState.code)
async def promo_apply(message: Message, state: FSMContext):
    code = message.text.strip()
    await state.clear()
    ok, msg, amount = await use_promo(code, message.from_user.id)
    if not ok:
        await message.answer(f"✕ {msg}")
        return
    await add_balance(message.from_user.id, amount)
    await message.answer(
        f"✓ Промокод сработал · <b>+{amount} {CURRENCY}</b> на баланс"
    )
