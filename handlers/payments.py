from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import (
    CRYPTOBOT_TOKEN,
    CURRENCY,
    REFERRAL_PERCENT,
    XROCKET_TOKEN,
)
from database import (
    add_balance,
    add_deposit,
    add_deposited,
    add_referral_earned,
    get_deposit,
    get_user,
    set_deposit_status,
)
from keyboards import back_kb, deposit_methods_kb, main_inline_kb, pay_kb
from providers import cryptobot, xrocket
from utils import LINE, send_menu

router = Router()

METHOD_NAMES = {"cryptobot": "CryptoBot", "xrocket": "xRocket"}


class DepositState(StatesGroup):
    amount = State()


DEPOSIT_TEXT = (
    f"⌁ <b>Пополнение</b>\n{LINE}\n"
    f"введи сумму в {CURRENCY} одним сообщением\n"
    "например: <code>10</code>"
)


async def _ask_amount(event, state: FSMContext):
    await state.set_state(DepositState.amount)
    await send_menu(event, DEPOSIT_TEXT, back_kb("menu"))


@router.message(F.text == "⌁ Пополнить")
async def deposit_msg(message: Message, state: FSMContext):
    await _ask_amount(message, state)


@router.callback_query(F.data == "deposit")
async def deposit_cb(cb: CallbackQuery, state: FSMContext):
    await _ask_amount(cb, state)
    await cb.answer()


@router.message(DepositState.amount)
async def deposit_amount(message: Message, state: FSMContext):
    raw = message.text.replace(",", ".").strip()
    try:
        amount = round(float(raw), 2)
    except ValueError:
        await message.answer("✕ Нужно число — например 10")
        return
    if amount <= 0:
        await message.answer("✕ Сумма должна быть больше нуля")
        return
    await state.update_data(amount=amount)
    await send_menu(
        message,
        f"к оплате · <b>{amount} {CURRENCY}</b>\n\n<i>чем будет удобнее оплатить?</i>",
        deposit_methods_kb(),
    )


@router.callback_query(F.data.startswith("depm:"))
async def deposit_method(cb: CallbackQuery, state: FSMContext):
    method = cb.data.split(":")[1]
    data = await state.get_data()
    amount = data.get("amount")
    await state.clear()
    if not amount:
        await cb.answer("Сначала укажи сумму", show_alert=True)
        return

    try:
        if method == "cryptobot":
            if not CRYPTOBOT_TOKEN:
                await cb.answer("CryptoBot не настроен", show_alert=True)
                return
            invoice = await cryptobot.create_invoice(
                amount, description=f"Пополнение {cb.from_user.id}", payload=str(cb.from_user.id)
            )
        else:
            if not XROCKET_TOKEN:
                await cb.answer("xRocket не настроен", show_alert=True)
                return
            invoice = await xrocket.create_invoice(
                amount, description=f"Пополнение {cb.from_user.id}", payload=str(cb.from_user.id)
            )
    except Exception as e:
        await cb.answer("✕ Не вышло создать счёт — попробуй позже", show_alert=True)
        return

    deposit_id = await add_deposit(cb.from_user.id, amount, method, invoice["id"])
    text = (
        f"⌁ <b>Счёт готов</b>\n{LINE}\n"
        f"сумма · <b>{amount} {CURRENCY}</b>\n"
        f"способ · {METHOD_NAMES.get(method, method)}\n\n"
        "1 · оплати по кнопке ниже\n"
        "2 · вернись и нажми «я оплатил»"
    )
    await send_menu(cb, text, pay_kb(deposit_id, invoice["url"]))
    await cb.answer()


async def _credit_deposit(bot: Bot, deposit):
    """Начисляет баланс и реферальный бонус."""
    uid = deposit["user_id"]
    amount = deposit["amount"]
    await add_balance(uid, amount)
    await add_deposited(uid, amount)

    user = await get_user(uid)
    if user and user["referrer_id"] and REFERRAL_PERCENT > 0:
        bonus = round(amount * REFERRAL_PERCENT / 100, 2)
        if bonus > 0:
            await add_balance(user["referrer_id"], bonus)
            await add_referral_earned(user["referrer_id"], bonus)
            try:
                await bot.send_message(
                    user["referrer_id"],
                    f"✦ реферальный бонус · <b>+{bonus} {CURRENCY}</b>",
                )
            except Exception:
                pass


@router.callback_query(F.data.startswith("checkdep:"))
async def check_deposit(cb: CallbackQuery, bot: Bot):
    dep_id = int(cb.data.split(":")[1])
    dep = await get_deposit(dep_id)
    if not dep or dep["user_id"] != cb.from_user.id:
        await cb.answer("Счёт не найден", show_alert=True)
        return
    if dep["status"] == "paid":
        await cb.answer("Этот счёт уже оплачен", show_alert=True)
        return

    try:
        if dep["method"] == "cryptobot":
            status = await cryptobot.check_invoice(dep["invoice_id"])
        else:
            status = await xrocket.check_invoice(dep["invoice_id"])
    except Exception:
        await cb.answer("✕ Не вышло проверить — попробуй позже", show_alert=True)
        return

    if status == "paid":
        await set_deposit_status(dep_id, "paid")
        await _credit_deposit(bot, dep)
        await send_menu(
            cb,
            f"✓ <b>Баланс пополнен</b>\n{LINE}\n"
            f"+{dep['amount']} {CURRENCY} уже на счёте — приятных покупок ⟡",
            main_inline_kb(),
        )
        await cb.answer("Оплата получена ⚡")
    else:
        await cb.answer(
            "оплата ещё не долетела — если платил только что, подожди минуту и проверь снова",
            show_alert=True,
        )
