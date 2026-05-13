from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class DjangoCatalogService:
    """Read-only adapter for the commerce Body catalog APIs."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    async def list_products(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/products/")
                if response.status_code == 200:
                    return response.json()
        except Exception as exc:
            logger.error("Failed to fetch products from Django Body: %s", exc)
        return []
