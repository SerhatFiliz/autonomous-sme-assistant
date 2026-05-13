from __future__ import annotations

import os

import httpx

from app.services.telemetry import add_log


class N8nService:
    """Client for delegated workflow automation in n8n."""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url or os.getenv("N8N_MARKET_WEBHOOK_URL")

    async def collect_market_prices(self, product_name: str) -> list[dict]:
        if not self.webhook_url:
            return []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(self.webhook_url, json={"product_name": product_name})
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            add_log("N8n Service", "amber", f"Market collector unavailable: {exc}")
            return []
        return data.get("competitors", data if isinstance(data, list) else [])

