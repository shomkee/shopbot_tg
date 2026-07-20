"""Интеграция с xRocket (xRocket Pay API).

Документация: https://pay.xrocket.tg/api/
Получить ключ: @xRocket -> Rocket Pay -> Create App / API key.
"""
import aiohttp

from config import XROCKET_ASSET, XROCKET_TOKEN

BASE = "https://pay.xrocket.tg"


def _headers():
    return {"Rocket-Pay-Key": XROCKET_TOKEN}


async def create_invoice(amount, description="", payload=""):
    """Создаёт счёт и возвращает {'id': ..., 'url': ...}."""
    data = {
        "amount": float(amount),
        "currency": XROCKET_ASSET,
        "description": description,
        "payload": payload,
        "numPayments": 1,
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{BASE}/tg-invoices", json=data, headers=_headers()) as r:
            res = await r.json()
    if not res.get("success"):
        raise RuntimeError(f"xRocket error: {res}")
    d = res["data"]
    return {
        "id": str(d["id"]),
        "url": d.get("link") or d.get("payLink") or d.get("url"),
    }


async def check_invoice(invoice_id):
    """Возвращает статус: 'paid' / 'active' / 'expired'."""
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{BASE}/tg-invoices/{invoice_id}", headers=_headers()) as r:
            res = await r.json()
    if not res.get("success"):
        return "active"
    d = res.get("data", {})
    status = d.get("status")
    if status:
        return status
    # запасной вариант: если оплачено хотя бы одним платежом
    if d.get("paid") or (d.get("activationsLeft") == 0):
        return "paid"
    return "active"
