"""Интеграция с CryptoBot (Crypto Pay API).

Документация: https://help.crypt.bot/crypto-pay-api
Получить токен: @CryptoBot -> Crypto Pay -> Create App.
"""
import aiohttp

from config import CRYPTOBOT_ASSET, CRYPTOBOT_TOKEN

BASE = "https://pay.crypt.bot/api"


def _headers():
    return {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}


async def create_invoice(amount, description="", payload=""):
    """Создаёт счёт и возвращает {'id': ..., 'url': ...}."""
    data = {
        "asset": CRYPTOBOT_ASSET,
        "amount": str(amount),
        "description": description,
        "payload": payload,
        "allow_comments": False,
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{BASE}/createInvoice", json=data, headers=_headers()) as r:
            res = await r.json()
    if not res.get("ok"):
        raise RuntimeError(f"CryptoBot error: {res}")
    inv = res["result"]
    return {
        "id": str(inv["invoice_id"]),
        "url": inv.get("bot_invoice_url") or inv.get("pay_url") or inv.get("web_app_invoice_url"),
    }


async def check_invoice(invoice_id):
    """Возвращает статус: 'paid' / 'active' / 'expired'."""
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{BASE}/getInvoices",
            params={"invoice_ids": str(invoice_id)},
            headers=_headers(),
        ) as r:
            res = await r.json()
    if not res.get("ok"):
        return "active"
    items = res.get("result", {}).get("items", [])
    if not items:
        return "active"
    return items[0].get("status", "active")
