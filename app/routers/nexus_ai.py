from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatPayload(BaseModel):
    store_slug: str
    message: str
    context: dict[str, Any] | None = None


def _products(context: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not context:
        return []
    return context.get("products", [])


@router.post("/manager/summary")
async def manager_summary(context: dict[str, Any], store: str | None = None) -> dict[str, Any]:
    products = _products(context)
    orders = context.get("orders", {})
    low_stock = [p for p in products if p.get("stock", 0) <= 10]
    slow = [p for p in products if p.get("stock", 0) >= 15 and p.get("sold_units", 0) <= 1]
    revenue = orders.get("revenue", 0)
    risks = []
    if low_stock:
        risks.append(f"{len(low_stock)} product(s) are close to stockout: " + ", ".join(p["name"] for p in low_stock[:3]))
    if orders.get("pending", 0):
        risks.append(f"{orders['pending']} pending orders need operational attention.")
    opportunities = []
    if slow:
        opportunities.append("Campaign opportunity on slow-moving stock: " + ", ".join(p["name"] for p in slow[:3]))
    if not opportunities:
        opportunities.append("Catalog is balanced; focus on margin-preserving bundles.")
    return {
        "summary": f"{context.get('store_name', store or 'Store')} has {len(products)} active variants and {revenue:.2f} revenue in the current demo dataset.",
        "risks": risks or ["No critical operational risk detected."],
        "opportunities": opportunities,
    }


@router.get("/manager/summary")
async def manager_summary_health(store: str | None = None) -> dict[str, Any]:
    return {
        "summary": f"{store or 'Store'} AI summary endpoint is reachable. Send POST with Django tenant context for live business analysis.",
        "risks": [],
        "opportunities": [],
    }


@router.post("/manager-advisor/chat")
async def manager_advisor(payload: ChatPayload) -> dict[str, Any]:
    products = _products(payload.context)
    text = payload.message.lower()
    if "stok" in text or "stock" in text:
        ranked = sorted(products, key=lambda p: p.get("stock", 0))[:3]
        answer = "Lowest stock products: " + "; ".join(f"{p['name']} ({p['stock']} units)" for p in ranked)
    elif "kar" in text or "profit" in text or "margin" in text:
        ranked = sorted(products, key=lambda p: p.get("margin", 0), reverse=True)[:3]
        answer = "Best margin products: " + "; ".join(f"{p['name']} ({p.get('margin', 0):.1f}% margin)" for p in ranked)
    elif "kampanya" in text or "campaign" in text:
        slow = [p for p in products if p.get("stock", 0) >= 15 and p.get("sold_units", 0) <= 1]
        answer = "Campaign candidates: " + (", ".join(p["name"] for p in slow[:3]) if slow else "No strong discount candidate; try bundles instead.")
    else:
        answer = f"I analyzed {len(products)} products for {payload.store_slug}. Ask about stock, campaign, profit margin, or restock planning."
    return {"answer": answer}


@router.post("/customer-assistant/chat")
async def customer_assistant(payload: ChatPayload) -> dict[str, Any]:
    products = _products(payload.context)
    text = payload.message.lower()
    answer_products = products
    if "ucuz" in text or "cheap" in text or "en ucuz" in text:
        answer_products = sorted(products, key=lambda p: p.get("price", 0))[:3]
        answer = "En uygun fiyatlı ürünler bunlar:"
    elif "stok" in text or "stock" in text:
        answer_products = [p for p in products if p.get("stock", 0) > 0][:3]
        answer = "Stokta olan öneriler:"
    else:
        answer_products = products[:3]
        answer = "Mağaza kataloğundan öneriler:"
    if "ucuz" in text or "cheap" in text or "en ucuz" in text:
        answer = "En uygun fiyatli urunler bunlar:"
    elif "stok" in text or "stock" in text:
        answer = "Stokta olan oneriler:"
    else:
        answer = "Magaza katalogundan oneriler:"
    return {"answer": answer, "products": answer_products}


@router.post("/campaigns/generate")
async def generate_campaigns(context: dict[str, Any]) -> dict[str, Any]:
    products = _products(context)
    today = date.today()
    events = [
        ("Mother's Day", date(today.year, 5, 10)),
        ("Summer Sale", date(today.year, 6, 15)),
        ("Black Friday", date(today.year, 11, 27)),
        ("New Year", date(today.year, 12, 25)),
    ]
    future_events = sorted(events, key=lambda item: abs((item[1] - today).days))
    event_name = future_events[0][0]
    candidates = sorted(products, key=lambda p: (p.get("sold_units", 0), -p.get("stock", 0)))[:4]
    campaigns = []
    for product in candidates:
        stock = product.get("stock", 0)
        sold = product.get("sold_units", 0)
        discount = 18 if stock >= 25 and sold <= 1 else 12
        old_price = float(product.get("price", 0))
        new_price = round(old_price * (100 - discount) / 100, 2)
        campaigns.append(
            {
                "product_id": product["product_id"],
                "variant_id": product["variant_id"],
                "product_name": product["name"],
                "reason": f"Stock is {stock} while recent sold units are {sold}; timed for {event_name}.",
                "event": event_name,
                "discount_percent": discount,
                "old_price": old_price,
                "new_price": new_price,
                "expected_impact": "Designed to convert slow-moving stock without over-discounting the catalog.",
            }
        )
    return {"campaigns": campaigns}


@router.get("/strategy-calendar")
async def strategy_calendar() -> dict[str, Any]:
    return {
        "suggestions": [
            {"event": "Mother's Day", "days_until": 30, "suggestion": "Promote giftable high-stock items with 12-18% discounts."},
            {"event": "Black Friday", "days_until": 180, "suggestion": "Reserve deep discounts for slow-moving inventory."},
        ]
    }
