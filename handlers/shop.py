from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import CURRENCY
from database import (
    add_balance,
    add_purchase,
    add_spent,
    get_categories,
    get_category,
    get_product,
    get_products,
    get_user,
    pop_item,
    stock_count,
)
from keyboards import categories_kb, category_kb, product_kb, purchased_kb
from utils import LINE, esc, send_menu

router = Router()


async def show_root_categories(event):
    cats = await get_categories(None)
    if not cats:
        await send_menu(
            event,
            f"⟡ <b>Витрина</b>\n{LINE}\nполки пока пустые — завоз уже в пути ⟢",
            categories_kb([]),
        )
        return
    await send_menu(
        event,
        f"⟡ <b>Витрина</b>\n{LINE}\n<i>выбери раздел:</i>",
        categories_kb(cats),
    )


@router.message(F.text == "⟡ Витрина")
async def buy_msg(message: Message):
    await show_root_categories(message)


@router.callback_query(F.data == "buy")
async def buy_cb(cb: CallbackQuery):
    await show_root_categories(cb)
    await cb.answer()


@router.callback_query(F.data.startswith("cat:"))
async def open_category(cb: CallbackQuery):
    cat_id = int(cb.data.split(":")[1])
    category = await get_category(cat_id)
    if not category:
        await cb.answer("Раздел не найден", show_alert=True)
        return
    subcats = await get_categories(cat_id)
    products = await get_products(cat_id)

    # куда ведёт кнопка «Назад»: к родительской категории или к списку категорий
    back_cb = f"cat:{category['parent_id']}" if category["parent_id"] else "buy"

    if not subcats and not products:
        await send_menu(
            cb,
            f"▸ <b>{esc(category['name'])}</b>\n{LINE}\nздесь пока пусто — загляни позже",
            category_kb([], [], back_cb),
        )
        await cb.answer()
        return

    await send_menu(
        cb,
        f"▸ <b>{esc(category['name'])}</b>\n{LINE}\n<i>выбери товар или раздел:</i>",
        category_kb(subcats, products, back_cb),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("prod:"))
async def open_product(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    product = await get_product(pid)
    if not product:
        await cb.answer("Товар не найден", show_alert=True)
        return
    stock = await stock_count(pid)
    desc = product["description"] or "описание скоро появится"
    text = (
        f"⟡ <b>{esc(product['name'])}</b>\n"
        f"{LINE}\n"
        f"{esc(desc)}\n\n"
        f"┌ цена · <b>{product['price']} {CURRENCY}</b>\n"
        f"└ в наличии · <b>{stock} шт</b>"
    )
    back_cb = f"cat:{product['category_id']}"
    # если у товара есть фото — показываем его (пункт ТЗ 11)
    await send_menu(cb, text, product_kb(pid, back_cb), photo=product["photo"] or None)
    await cb.answer()


@router.callback_query(F.data.startswith("buyprod:"))
async def buy_product(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    product = await get_product(pid)
    if not product:
        await cb.answer("Товар не найден", show_alert=True)
        return
    user = await get_user(cb.from_user.id)
    if await stock_count(pid) <= 0:
        await cb.answer("✕ Товар разобрали — загляни позже", show_alert=True)
        return
    if user["balance"] < product["price"]:
        await cb.answer(
            "✕ Не хватает на балансе — пополни и возвращайся", show_alert=True
        )
        return
    item = await pop_item(pid)
    if not item:
        await cb.answer("✕ Товар разобрали — загляни позже", show_alert=True)
        return

    await add_balance(cb.from_user.id, -product["price"])
    await add_spent(cb.from_user.id, product["price"])
    purchase_id = await add_purchase(
        cb.from_user.id, pid, item["id"], product["name"], product["price"], item["content"]
    )

    text = (
        f"✓ <b>Оплачено — товар твой</b>\n"
        f"{LINE}\n"
        f"⟡ {esc(product['name'])}\n"
        f"⌁ списано · <b>{product['price']} {CURRENCY}</b>\n\n"
        "твой товар:\n"
        f"<code>{esc(item['content'])}</code>\n\n"
        "<i>файл с покупкой всегда можно забрать в кабинете</i>"
    )
    await send_menu(cb, text, purchased_kb(purchase_id))
    await cb.answer("Готово ⚡")
