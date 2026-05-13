from __future__ import annotations

import random
from dataclasses import dataclass

from app.services.django_catalog_service import DjangoCatalogService
from app.services.telemetry import add_log


@dataclass
class StockPrediction:
    product_id: int
    product_name: str
    current_stock: int
    days_until_depletion: int
    suggested_restock_quantity: int
    optimal_purchase_price: float


class SupplyChainAgent:
    """Read-only inventory intelligence over catalog data."""

    def predict_stock(self, products) -> list[StockPrediction]:
        predictions = []
        for product in products:
            stock_quantity = getattr(product, "stock_quantity", product.get("stock_quantity", 0) if isinstance(product, dict) else 0)
            price = float(getattr(product, "price", product.get("price", 0) if isinstance(product, dict) else 0))
            name = getattr(product, "name", product.get("name", "Product") if isinstance(product, dict) else "Product")
            product_id = getattr(product, "id", product.get("id", 0) if isinstance(product, dict) else 0)
            daily_sales_rate = random.uniform(0.5, 3.0)
            days_until = int(stock_quantity / daily_sales_rate) if stock_quantity > 0 else 0
            suggested_restock = max(int(daily_sales_rate * 30), 10)
            predictions.append(
                StockPrediction(
                    product_id=product_id,
                    product_name=name,
                    current_stock=stock_quantity,
                    days_until_depletion=days_until,
                    suggested_restock_quantity=suggested_restock,
                    optimal_purchase_price=round(price * random.uniform(0.4, 0.6), 2),
                )
            )
        return predictions

    async def run_background_check(self) -> None:
        add_log("SupplyChainAgent", "indigo", "Reading inventory signals from Django Body catalog API.")
        products = await DjangoCatalogService().list_products()
        low_stock = [p for p in products if p.get("variants") and any(v.get("stock_quantity", 0) < 10 for v in p["variants"])]
        if low_stock:
            add_log("SupplyChainAgent", "indigo", f"Critical low stock: {low_stock[0]['name']}. Recommended restock: 50 units.")
            return
        add_log("SupplyChainAgent", "indigo", "All inventory signals healthy.")

