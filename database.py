import time
import aiosqlite

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    balance REAL DEFAULT 0,
    total_spent REAL DEFAULT 0,
    total_deposited REAL DEFAULT 0,
    referrer_id INTEGER,
    referral_earned REAL DEFAULT 0,
    is_blocked INTEGER DEFAULT 0,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    photo TEXT,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS product_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    is_sold INTEGER DEFAULT 0,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER,
    item_id INTEGER,
    product_name TEXT,
    price REAL,
    content TEXT,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    method TEXT,
    invoice_id TEXT,
    status TEXT DEFAULT 'pending',
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS promocodes (
    code TEXT PRIMARY KEY,
    amount REAL NOT NULL,
    activations INTEGER DEFAULT 1,
    used INTEGER DEFAULT 0,
    created_at INTEGER
);

CREATE TABLE IF NOT EXISTS promo_uses (
    code TEXT,
    user_id INTEGER,
    PRIMARY KEY (code, user_id)
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


# ============ ПОЛЬЗОВАТЕЛИ ============
async def get_or_create_user(user_id, username, full_name, referrer_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET username=?, full_name=? WHERE user_id=?",
                (username, full_name, user_id),
            )
            await db.commit()
            return dict(row), False
        ref = None
        if referrer_id and referrer_id != user_id:
            c2 = await db.execute("SELECT 1 FROM users WHERE user_id=?", (referrer_id,))
            if await c2.fetchone():
                ref = referrer_id
        await db.execute(
            "INSERT INTO users (user_id, username, full_name, referrer_id, created_at) "
            "VALUES (?,?,?,?,?)",
            (user_id, username, full_name, ref, int(time.time())),
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return dict(await cur.fetchone()), True


async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def add_balance(user_id, delta):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, user_id)
        )
        await db.commit()


async def add_spent(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_spent = total_spent + ? WHERE user_id=?",
            (amount, user_id),
        )
        await db.commit()


async def add_deposited(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET total_deposited = total_deposited + ? WHERE user_id=?",
            (amount, user_id),
        )
        await db.commit()


async def add_referral_earned(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET referral_earned = referral_earned + ? WHERE user_id=?",
            (amount, user_id),
        )
        await db.commit()


async def set_blocked(user_id, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked=? WHERE user_id=?", (1 if value else 0, user_id)
        )
        await db.commit()


async def count_referrals(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM users WHERE referrer_id=?", (user_id,)
        )
        return (await cur.fetchone())[0]


# ============ КАТЕГОРИИ ============
async def add_category(name, parent_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO categories (name, parent_id) VALUES (?,?)", (name, parent_id)
        )
        await db.commit()
        return cur.lastrowid


async def get_categories(parent_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if parent_id is None:
            cur = await db.execute(
                "SELECT * FROM categories WHERE parent_id IS NULL ORDER BY name"
            )
        else:
            cur = await db.execute(
                "SELECT * FROM categories WHERE parent_id=? ORDER BY name", (parent_id,)
            )
        return [dict(r) for r in await cur.fetchall()]


async def get_all_categories():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM categories ORDER BY parent_id, name")
        return [dict(r) for r in await cur.fetchall()]


async def get_category(cat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM categories WHERE id=?", (cat_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


# ============ ТОВАРЫ ============
async def add_product(category_id, name, description, price, photo=None):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO products (category_id, name, description, price, photo, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (category_id, name, description, price, photo, int(time.time())),
        )
        await db.commit()
        return cur.lastrowid


async def get_products(category_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM products WHERE category_id=? ORDER BY name", (category_id,)
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_all_products():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products ORDER BY name")
        return [dict(r) for r in await cur.fetchall()]


async def get_product(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products WHERE id=?", (product_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


# ============ СТОК (единицы товара) ============
async def add_item(product_id, content):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO product_items (product_id, content, created_at) VALUES (?,?,?)",
            (product_id, content, int(time.time())),
        )
        await db.commit()


async def stock_count(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM product_items WHERE product_id=? AND is_sold=0",
            (product_id,),
        )
        return (await cur.fetchone())[0]


async def pop_item(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM product_items WHERE product_id=? AND is_sold=0 LIMIT 1",
            (product_id,),
        )
        row = await cur.fetchone()
        if not row:
            return None
        await db.execute("UPDATE product_items SET is_sold=1 WHERE id=?", (row["id"],))
        await db.commit()
        return dict(row)


# ============ ПОКУПКИ ============
async def add_purchase(user_id, product_id, item_id, product_name, price, content):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO purchases (user_id, product_id, item_id, product_name, price, content, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (user_id, product_id, item_id, product_name, price, content, int(time.time())),
        )
        await db.commit()
        return cur.lastrowid


async def get_purchases(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM purchases WHERE user_id=? ORDER BY id DESC", (user_id,)
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_purchase(purchase_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


# ============ ДЕПОЗИТЫ ============
async def add_deposit(user_id, amount, method, invoice_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO deposits (user_id, amount, method, invoice_id, created_at) "
            "VALUES (?,?,?,?,?)",
            (user_id, amount, method, invoice_id, int(time.time())),
        )
        await db.commit()
        return cur.lastrowid


async def get_deposit(deposit_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM deposits WHERE id=?", (deposit_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_deposit_status(deposit_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE deposits SET status=? WHERE id=?", (status, deposit_id)
        )
        await db.commit()


# ============ ПРОМОКОДЫ ============
async def add_promo(code, amount, activations):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO promocodes (code, amount, activations, used, created_at) "
            "VALUES (?,?,?,0,?)",
            (code, amount, activations, int(time.time())),
        )
        await db.commit()


async def use_promo(code, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM promocodes WHERE code=?", (code,))
        p = await cur.fetchone()
        if not p:
            return False, "Промокод не найден.", 0
        if p["used"] >= p["activations"]:
            return False, "Промокод исчерпан.", 0
        c2 = await db.execute(
            "SELECT 1 FROM promo_uses WHERE code=? AND user_id=?", (code, user_id)
        )
        if await c2.fetchone():
            return False, "Вы уже активировали этот промокод.", 0
        await db.execute(
            "INSERT INTO promo_uses (code, user_id) VALUES (?,?)", (code, user_id)
        )
        await db.execute("UPDATE promocodes SET used = used + 1 WHERE code=?", (code,))
        await db.commit()
        return True, "ok", p["amount"]


# ============ СТАТИСТИКА ============
async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async def one(q):
            cur = await db.execute(q)
            return (await cur.fetchone())[0]

        return {
            "users": await one("SELECT COUNT(*) FROM users"),
            "blocked": await one("SELECT COUNT(*) FROM users WHERE is_blocked=1"),
            "products": await one("SELECT COUNT(*) FROM products"),
            "stock": await one("SELECT COUNT(*) FROM product_items WHERE is_sold=0"),
            "purchases": await one("SELECT COUNT(*) FROM purchases"),
            "revenue": await one("SELECT COALESCE(SUM(price),0) FROM purchases"),
            "deposited": await one(
                "SELECT COALESCE(SUM(amount),0) FROM deposits WHERE status='paid'"
            ),
        }
