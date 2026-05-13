from __future__ import annotations

import random
from statistics import mean

from app.services.n8n_service import N8nService
from app.services.telemetry import add_log


class MarketIntelligenceAgent:
    """Competitor pricing intelligence without owning sales transactions."""

    def __init__(self, collector: N8nService | None = None):
        self.collector = collector or N8nService()

    async def analyze(self, product_name: str, cost_price: float, target_profit_margin: float, currency: str = "TRY") -> dict:
        competitors = await self.collector.collect_market_prices(product_name)
        if not competitors:
            competitors = self._simulated_competitors(product_name)

        prices = [float(item["price"]) for item in competitors if "price" in item]
        if not prices:
            prices = [cost_price * 1.3]

        minimum_margin_price = cost_price / (1 - target_profit_margin / 100) if target_profit_margin < 100 else cost_price
        market_average = mean(prices)
        recommended = max(minimum_margin_price, market_average * 0.98)
        result = {
            "product_name": product_name,
            "currency": currency,
            "competitors": competitors,
            "lowest_price": round(min(prices), 2),
            "highest_price": round(max(prices), 2),
            "average_price": round(market_average, 2),
            "recommended_selling_price": round(recommended, 2),
            "rationale": "Balances competitor average with the store target margin floor.",
        }
        add_log("MarketIntelligenceAgent", "cyan", f"Analyzed {product_name}: recommended {result['recommended_selling_price']} {currency}")
        return result

    @staticmethod
    def _simulated_competitors(product_name: str) -> list[dict]:
        seed = sum(ord(char) for char in product_name)
        random.seed(seed)
        base = random.uniform(250, 1200)
        return [
            {"source": "Cimri simulated", "price": round(base * random.uniform(0.86, 1.1), 2)},
            {"source": "Akakce simulated", "price": round(base * random.uniform(0.9, 1.18), 2)},
            {"source": "Marketplace SERP simulated", "price": round(base * random.uniform(0.82, 1.25), 2)},
        ]

