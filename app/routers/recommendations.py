from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/recommendations/cross-sell", tags=["Smart Customer Engine"])
async def cross_sell(sku: str):
    return {
        "source_sku": sku,
        "recommendations": [
            {"sku": "ACC-001", "name": "Premium Protection Case", "reason": "Semantic similarity and high co-occurrence"},
            {"sku": "ACC-002", "name": "Extended Warranty", "reason": "High attachment rate"},
        ],
    }


@router.post("/recommendations/cart-nudge", tags=["Smart Customer Engine"])
async def cart_nudge(payload: dict):
    discount = "10%" if payload.get("cart_total", 0) > 100 else "5%"
    return {
        "nudge_message": f"Complete your purchase in the next 5 minutes for an extra {discount} off!",
        "discount_code": "FOMO5",
    }
