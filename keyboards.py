from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import CURRENCY


# ==== Reply-клавиатура (пункт ТЗ 12: основные кнопки под клавиатурой) ====
def main_menu_kb(is_admin=False):
    b = ReplyKeyboardBuilder()
    b.button(text="⟡ Витрина")
    b.button(text="⌁ Пополнить")
    b.button(text="⌘ Кабинет")
    b.button(text="✆ Поддержка")
    if is_admin:
        b.button(text="▲ Панель")
        b.adjust(2, 2, 1)
    else:
        b.adjust(2, 2)
    return b.as_markup(resize_keyboard=True)


# ==== Inline-меню ====
def main_inline_kb():
    b = InlineKeyboardBuilder()
    b.button(text="⟡ Витрина", callback_data="buy")
    b.button(text="⌁ Пополнить", callback_data="deposit")
    b.button(text="⌘ Кабинет", callback_data="profile")
    b.button(text="✆ Поддержка", callback_data="support")
    b.adjust(2, 2)
    return b.as_markup()


def back_kb(cb="menu"):
    b = InlineKeyboardBuilder()
    b.button(text="‹ назад", callback_data=cb)
    return b.as_markup()


def categories_kb(cats, back_cb="menu"):
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=f"▸ {c['name']}", callback_data=f"cat:{c['id']}")
    b.button(text="‹ назад", callback_data=back_cb)
    b.adjust(1)
    return b.as_markup()


def category_kb(subcats, products, back_cb="buy"):
    b = InlineKeyboardBuilder()
    for c in subcats:
        b.button(text=f"▸ {c['name']}", callback_data=f"cat:{c['id']}")
    for p in products:
        b.button(
            text=f"⟡ {p['name']} · {p['price']} {CURRENCY}",
            callback_data=f"prod:{p['id']}",
        )
    b.button(text="‹ назад", callback_data=back_cb)
    b.adjust(1)
    return b.as_markup()


def product_kb(product_id, back_cb):
    b = InlineKeyboardBuilder()
    b.button(text="⚡ Забрать сейчас", callback_data=f"buyprod:{product_id}")
    b.button(text="‹ назад", callback_data=back_cb)
    b.adjust(1)
    return b.as_markup()


def purchased_kb(purchase_id):
    b = InlineKeyboardBuilder()
    b.button(text="⇩ Скачать файлом", callback_data=f"export:{purchase_id}")
    b.button(text="⟡ В витрину", callback_data="buy")
    b.adjust(1)
    return b.as_markup()


def profile_kb():
    b = InlineKeyboardBuilder()
    b.button(text="≡ Мои покупки", callback_data="history:0")
    b.button(text="✦ Рефералы", callback_data="ref")
    b.button(text="⚿ Промокод", callback_data="promo")
    b.button(text="‹ назад", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def history_kb(purchases, page, total_pages):
    b = InlineKeyboardBuilder()
    for p in purchases:
        b.button(
            text=f"⇩ #{p['id']} · {p['product_name']}",
            callback_data=f"export:{p['id']}",
        )
    nav = []
    if page > 0:
        b.button(text="‹", callback_data=f"history:{page - 1}")
        nav.append(1)
    if page < total_pages - 1:
        b.button(text="›", callback_data=f"history:{page + 1}")
        nav.append(1)
    b.button(text="⌘ в кабинет", callback_data="profile")
    # каждая кнопка экспорта — на своей строке, навигация и назад — отдельно
    b.adjust(*([1] * len(purchases) + ([len(nav)] if nav else []) + [1]))
    return b.as_markup()


def deposit_methods_kb():
    b = InlineKeyboardBuilder()
    b.button(text="◈ xRocket", callback_data="depm:xrocket")
    b.button(text="◈ CryptoBot", callback_data="depm:cryptobot")
    b.button(text="‹ назад", callback_data="menu")
    b.adjust(2, 1)
    return b.as_markup()


def pay_kb(deposit_id, url):
    b = InlineKeyboardBuilder()
    b.button(text="⚡ Оплатить", url=url)
    b.button(text="↻ Я оплатил — проверить", callback_data=f"checkdep:{deposit_id}")
    b.button(text="‹ назад", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def support_kb():
    b = InlineKeyboardBuilder()
    b.button(text="§ Правила", callback_data="rules")
    b.button(text="‹ назад", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def admin_kb(is_owner=False):
    b = InlineKeyboardBuilder()
    b.button(text="＋ Категория", callback_data="adm:addcat")
    b.button(text="＋ Подкатегория", callback_data="adm:addsub")
    b.button(text="＋ Товар", callback_data="adm:addproduct")
    b.button(text="＋ Сток", callback_data="adm:addstock")
    if is_owner:
        b.button(text="⚿ Создать промокод", callback_data="adm:newpromo")
    b.button(text="⌁ Выдать баланс", callback_data="adm:givebal")
    b.button(text="✕ Заблокировать", callback_data="adm:block")
    b.button(text="○ Разблокировать", callback_data="adm:unblock")
    b.button(text="∑ Статистика", callback_data="adm:stats")
    b.button(text="‹ назад", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


def pick_kb(items, prefix, back_cb="admin"):
    """Список объектов для выбора в админке (категории/товары)."""
    b = InlineKeyboardBuilder()
    for it in items:
        b.button(text=it["label"], callback_data=f"{prefix}:{it['id']}")
    b.button(text="‹ назад", callback_data=back_cb)
    b.adjust(1)
    return b.as_markup()
