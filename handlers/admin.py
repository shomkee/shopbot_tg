from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from config import CURRENCY, is_admin, is_owner
from database import (
    add_category,
    add_item,
    add_product,
    add_promo,
    add_balance,
    get_all_categories,
    get_all_products,
    get_category,
    get_product,
    get_stats,
    get_user,
    set_blocked,
)
from keyboards import admin_kb, back_kb, pick_kb
from utils import LINE, esc, send_menu

router = Router()


# ================= FSM =================
class AddCat(StatesGroup):
    name = State()


class AddSub(StatesGroup):
    parent = State()
    name = State()


class AddProduct(StatesGroup):
    category = State()
    name = State()
    desc = State()
    price = State()
    photo = State()
    stock = State()


class AddStock(StatesGroup):
    product = State()
    lines = State()


class NewPromo(StatesGroup):
    code = State()
    amount = State()
    acts = State()


class GiveBal(StatesGroup):
    uid = State()
    amount = State()


class BlockU(StatesGroup):
    uid = State()


class UnblockU(StatesGroup):
    uid = State()


# ============ helpers ============
def _cat_label(cat, cats_by_id):
    if cat["parent_id"] and cat["parent_id"] in cats_by_id:
        return f"{cats_by_id[cat['parent_id']]['name']} › {cat['name']}"
    return cat["name"]


async def _guard(event):
    uid = event.from_user.id
    if not is_admin(uid):
        if isinstance(event, CallbackQuery):
            await event.answer("Нет доступа", show_alert=True)
        return False
    return True


async def show_admin(event):
    text = (
        f"▲ <b>Панель управления</b>\n{LINE}\n<i>выбери действие:</i>"
    )
    await send_menu(event, text, admin_kb(is_owner(event.from_user.id)))


# ============ вход в админку ============
@router.message(F.text == "▲ Панель")
async def admin_msg(message: Message, state: FSMContext):
    if not await _guard(message):
        return
    await state.clear()
    await show_admin(message)


@router.callback_query(F.data == "admin")
async def admin_cb(cb: CallbackQuery, state: FSMContext):
    if not await _guard(cb):
        return
    await state.clear()
    await show_admin(cb)
    await cb.answer()


# ============ отмена ============
@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    await show_admin(message)


# ============ ДОБАВИТЬ КАТЕГОРИЮ ============
@router.callback_query(F.data == "adm:addcat")
async def addcat_start(cb: CallbackQuery, state: FSMContext):
    if not await _guard(cb):
        return
    await state.set_state(AddCat.name)
    await send_menu(cb, "＋ Название новой категории:", back_kb("admin"))
    await cb.answer()


@router.message(AddCat.name)
async def addcat_finish(message: Message, state: FSMContext):
    await add_category(message.text.strip(), None)
    await state.clear()
    await message.answer(f"✓ Категория «{esc(message.text.strip())}» создана.")
    await show_admin(message)


# ============ ДОБАВИТЬ ПОДКАТЕГОРИЮ ============
@router.callback_query(F.data == "adm:addsub")
async def addsub_start(cb: CallbackQuery, state: FSMContext):
    if not await _guard(cb):
        return
    cats = await get_all_categories()
    if not cats:
        await cb.answer("Сначала создайте категорию", show_alert=True)
        return
    by_id = {c["id"]: c for c in cats}
    items = [{"id": c["id"], "label": _cat_label(c, by_id)} for c in cats]
    await state.set_state(AddSub.parent)
    await send_menu(
        cb, "＋ Родительская категория:", pick_kb(items, "admsubp")
    )
    await cb.answer()


@router.callback_query(AddSub.parent, F.data.startswith("admsubp:"))
async def addsub_parent(cb: CallbackQuery, state: FSMContext):
    parent_id = int(cb.data.split(":")[1])
    await state.update_data(parent=parent_id)
    await state.set_state(AddSub.name)
    await send_menu(cb, "＋ Название подкатегории:", back_kb("admin"))
    await cb.answer()


@router.message(AddSub.name)
async def addsub_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    await add_category(message.text.strip(), data["parent"])
    await state.clear()
    await message.answer(f"✓ Подкатегория «{esc(message.text.strip())}» создана.")
    await show_admin(message)


# ============ ДОБАВИТЬ ТОВАР (пункт ТЗ 7, 11) ============
@router.callback_query(F.data == "adm:addproduct")
async def addproduct_start(cb: CallbackQuery, state: FSMContext):
    if not await _guard(cb):
        return
    cats = await get_all_categories()
    if not cats:
        await cb.answer("Сначала создайте категорию", show_alert=True)
        return
    by_id = {c["id"]: c for c in cats}
    items = [{"id": c["id"], "label": _cat_label(c, by_id)} for c in cats]
    await state.set_state(AddProduct.category)
    await send_menu(
        cb, "＋ В какой раздел добавить товар?", pick_kb(items, "admprodc")
    )
    await cb.answer()


@router.callback_query(AddProduct.category, F.data.startswith("admprodc:"))
async def addproduct_category(cb: CallbackQuery, state: FSMContext):
    await state.update_data(category=int(cb.data.split(":")[1]))
    await state.set_state(AddProduct.name)
    await send_menu(cb, "＋ Название товара:", back_kb("admin"))
    await cb.answer()


@router.message(AddProduct.name)
async def addproduct_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProduct.desc)
    await message.answer(
        "✎ Описание товара (или «-», чтобы пропустить):"
    )


@router.message(AddProduct.desc)
async def addproduct_desc(message: Message, state: FSMContext):
    desc = message.text.strip()
    if desc == "-":
        desc = ""
    await state.update_data(desc=desc)
    await state.set_state(AddProduct.price)
    await message.answer(f"⌁ Цена товара в {CURRENCY} (например 5.5):")


@router.message(AddProduct.price)
async def addproduct_price(message: Message, state: FSMContext):
    try:
        price = round(float(message.text.replace(",", ".").strip()), 2)
    except ValueError:
        await message.answer("✕ Введите число, например 5.5")
        return
    await state.update_data(price=price)
    await state.set_state(AddProduct.photo)
    await message.answer(
        "▣ Фото товара (по желанию) или «-», чтобы пропустить:"
    )


@router.message(AddProduct.photo, F.photo)
async def addproduct_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await _create_product(message, state, photo_id)


@router.message(AddProduct.photo)
async def addproduct_photo_skip(message: Message, state: FSMContext):
    await _create_product(message, state, None)


async def _create_product(message, state, photo_id):
    data = await state.get_data()
    product_id = await add_product(
        data["category"], data["name"], data["desc"], data["price"], photo_id
    )
    await state.update_data(product=product_id)
    await state.set_state(AddProduct.stock)
    await message.answer(
        "✓ Товар создан!\n\n"
        "▤ Теперь отправьте единицы товара (аккаунты/ключи/текст).\n"
        "Каждая строка = одна единица товара.\n"
        "Если стока пока нет — отправьте «-»."
    )


@router.message(AddProduct.stock)
async def addproduct_stock(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    text = message.text.strip()
    if text == "-":
        await message.answer("Товар создан без стока. Добавить можно через «Добавить сток».")
        await show_admin(message)
        return
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines:
        await add_item(data["product"], line)
    await message.answer(f"✓ Добавлено единиц товара: <b>{len(lines)}</b>.")
    await show_admin(message)


# ============ ДОБАВИТЬ СТОК К СУЩЕСТВУЮЩЕМУ ТОВАРУ ============
@router.callback_query(F.data == "adm:addstock")
async def addstock_start(cb: CallbackQuery, state: FSMContext):
    if not await _guard(cb):
        return
    products = await get_all_products()
    if not products:
        await cb.answer("Сначала создайте товар", show_alert=True)
        return
    items = [
        {"id": p["id"], "label": f"{p['name']} ({p['price']} {CURRENCY})"}
        for p in products
    ]
    await state.set_state(AddStock.product)
    await send_menu(cb, "▤ К какому товару добавить сток?", pick_kb(items, "admstockp"))
    await cb.answer()


@router.callback_query(AddStock.product, F.data.startswith("admstockp:"))
async def addstock_product(cb: CallbackQuery, state: FSMContext):
    await state.update_data(product=int(cb.data.split(":")[1]))
    await state.set_state(AddStock.lines)
    await send_menu(
        cb,
        "▤ Отправьте единицы товара — каждая с новой строки:",
        back_kb("admin"),
    )
    await cb.answer()


@router.message(AddStock.lines)
async def addstock_lines(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    lines = [l.strip() for l in message.text.split("\n") if l.strip()]
    for line in lines:
        await add_item(data["product"], line)
    await message.answer(f"✓ Добавлено единиц товара: <b>{len(lines)}</b>.")
    await show_admin(message)


# ============ СОЗДАТЬ ПРОМОКОД (только владелец, пункт ТЗ 6) ============
@router.callback_query(F.data == "adm:newpromo")
async def newpromo_start(cb: CallbackQuery, state: FSMContext):
    if not is_owner(cb.from_user.id):
        await cb.answer("Промокоды может создавать только владелец.", show_alert=True)
        return
    await state.set_state(NewPromo.code)
    await send_menu(cb, "⚿ Код промокода (например SALE10):", back_kb("admin"))
    await cb.answer()


@router.message(NewPromo.code)
async def newpromo_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await state.set_state(NewPromo.amount)
    await message.answer(f"⌁ На какую сумму промокод (в {CURRENCY})?")


@router.message(NewPromo.amount)
async def newpromo_amount(message: Message, state: FSMContext):
    try:
        amount = round(float(message.text.replace(",", ".").strip()), 2)
    except ValueError:
        await message.answer("✕ Введите число")
        return
    await state.update_data(amount=amount)
    await state.set_state(NewPromo.acts)
    await message.answer("↻ Сколько раз можно активировать промокод?")


@router.message(NewPromo.acts)
async def newpromo_acts(message: Message, state: FSMContext):
    try:
        acts = int(message.text.strip())
    except ValueError:
        await message.answer("✕ Введите целое число")
        return
    data = await state.get_data()
    await state.clear()
    await add_promo(data["code"], data["amount"], acts)
    await message.answer(
        f"✓ Промокод <code>{esc(data['code'])}</code> на {data['amount']} {CURRENCY} "
        f"создан ({acts} активаций)."
    )
    await show_admin(message)


# ============ ВЫДАТЬ БАЛАНС (пункт ТЗ 7) ============
@router.callback_query(F.data == "adm:givebal")
async def givebal_start(cb: CallbackQuery, state: FSMContext):
    if not await _guard(cb):
        return
    await state.set_state(GiveBal.uid)
    await send_menu(cb, "⌁ ID пользователя:", back_kb("admin"))
    await cb.answer()


@router.message(GiveBal.uid)
async def givebal_uid(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("✕ ID — это число")
        return
    if not await get_user(uid):
        await message.answer("✕ Пользователь не найден (он должен хотя бы раз запустить бота)")
        return
    await state.update_data(uid=uid)
    await state.set_state(GiveBal.amount)
    await message.answer("⌁ На сколько изменить баланс? (можно отрицательное, напр. -5)")


@router.message(GiveBal.amount)
async def givebal_amount(message: Message, state: FSMContext, bot: Bot):
    try:
        amount = round(float(message.text.replace(",", ".").strip()), 2)
    except ValueError:
        await message.answer("✕ Введите число")
        return
    data = await state.get_data()
    await state.clear()
    await add_balance(data["uid"], amount)
    await message.answer(
        f"✓ Баланс пользователя <code>{data['uid']}</code> изменён на {amount} {CURRENCY}."
    )
    try:
        await bot.send_message(
            data["uid"], f"⌁ Баланс изменён администрацией · {amount} {CURRENCY}"
        )
    except Exception:
        pass
    await show_admin(message)


# ============ БЛОКИРОВКА / РАЗБЛОКИРОВКА (пункт ТЗ 7) ============
@router.callback_query(F.data == "adm:block")
async def block_start(cb: CallbackQuery, state: FSMContext):
    if not await _guard(cb):
        return
    await state.set_state(BlockU.uid)
    await send_menu(cb, "✕ ID пользователя для блокировки:", back_kb("admin"))
    await cb.answer()


@router.message(BlockU.uid)
async def block_finish(message: Message, state: FSMContext):
    await state.clear()
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("✕ ID — это число")
        return
    await set_blocked(uid, True)
    await message.answer(f"✕ Пользователь <code>{uid}</code> заблокирован.")
    await show_admin(message)


@router.callback_query(F.data == "adm:unblock")
async def unblock_start(cb: CallbackQuery, state: FSMContext):
    if not await _guard(cb):
        return
    await state.set_state(UnblockU.uid)
    await send_menu(cb, "○ ID пользователя для разблокировки:", back_kb("admin"))
    await cb.answer()


@router.message(UnblockU.uid)
async def unblock_finish(message: Message, state: FSMContext):
    await state.clear()
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("✕ ID — это число")
        return
    await set_blocked(uid, False)
    await message.answer(f"○ Пользователь <code>{uid}</code> разблокирован.")
    await show_admin(message)


# ============ СТАТИСТИКА ============
@router.callback_query(F.data == "adm:stats")
async def stats_cb(cb: CallbackQuery):
    if not await _guard(cb):
        return
    s = await get_stats()
    text = (
        f"∑ <b>Статистика</b>\n{LINE}\n"
        f"пользователей · <b>{s['users']}</b> (в бане: {s['blocked']})\n"
        f"товаров · <b>{s['products']}</b> (единиц в стоке: {s['stock']})\n"
        f"покупок · <b>{s['purchases']}</b>\n"
        f"{LINE}\n"
        f"выручка · <b>{round(s['revenue'], 2)} {CURRENCY}</b>\n"
        f"депозитов · <b>{round(s['deposited'], 2)} {CURRENCY}</b>"
    )
    await send_menu(cb, text, back_kb("admin"))
    await cb.answer()
