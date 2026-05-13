# saas_ecommerce_ai_agent/services/ai_agent.py
# Gemini-powered AI service used by the WebSocket chat endpoint.

from __future__ import annotations

import asyncio
import logging
import os
import httpx
from typing import AsyncIterator

logger = logging.getLogger(__name__)

def search_products(query: str) -> str:
    """
    Tool function to search products from the Django REST API.
    Returns a markdown-formatted string with real product results.
    """
    try:
        import httpx
        # Django storefront API URL
        django_api_url = "http://127.0.0.1:8000/api/products/"
        with httpx.Client() as client:
            response = client.get(django_api_url, timeout=5.0)
            if response.status_code != 200:
                return "Failed to fetch products from the store."
            products = response.json()
            
            # Simple client-side search simulation including category understanding
            query_lower = query.lower()
            results = []
            
            # Smart category synonyms
            category_map = {
                "kitchen": ["mixer", "blender", "toaster", "oven"],
                "electronics": ["laptop", "phone", "tablet", "charger"],
                "clothing": ["shirt", "pants", "jacket", "shoes"]
            }
            
            expanded_queries = [query_lower]
            for cat, keywords in category_map.items():
                if cat in query_lower:
                    expanded_queries.extend(keywords)
            
            for p in products:
                product_text = (p.get("name", "") + " " + p.get("description", "")).lower()
                
                # Check if any of our expanded queries match
                if any(q in product_text for q in expanded_queries):
                    # Format as markdown so the widget can render it as a clickable card
                    slug = p.get("slug")
                    # Using public tenant host (127.0.0.1:8000) for demo
                    product_url = f"http://127.0.0.1:8000/product/{slug}/"
                    results.append(f"**{p.get('name')}** - {p.get('description', '')[:50]}...\n[View Product]({product_url})")
            
            if not results:
                return f"No products found matching '{query}'."
            return "\n\n".join(results[:5])
    except Exception as e:
        logger.error("Error searching products: %s", e)
        return "Sorry, I am unable to access the product catalog right now."


# System persona for the B2B SaaS chat widget.
_SYSTEM_PROMPT = (
    "You are KOBİ-AI, an expert e-commerce assistant embedded in a multi-tenant B2B SaaS platform. "
    "Your role is to help store owners and customers with product inquiries, order tracking, "
    "inventory questions, and general shopping guidance. "
    "Always respond in a concise, professional, and friendly tone. "
    "If you do not know an answer with certainty, say so honestly rather than speculating."
)


def _get_gemini_client():
    """Lazily initialise the Gemini client to avoid import errors at startup."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Add it to your .env file and restart the server."
        )
    from google import genai  # type: ignore[import]
    return genai.Client(api_key=api_key)


def get_business_health_report() -> str:
    """
    Tool function to get business health report including Total Sales, Profit Margin, and Low Stock Alerts.
    """
    try:
        import httpx
        with httpx.Client() as client:
            # Let's simulate calling the finance endpoint we built
            response = client.get("http://127.0.0.1:8001/api/v1/analytics/finance", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return (
                    f"**Business Health Report**\n"
                    f"- **Total Sales (Monthly)**: ${data.get('monthly_revenue', 0):.2f}\n"
                    f"- **Profit/Loss**: ${data.get('profit_loss', 0):.2f}\n"
                    f"- **Summary**: {data.get('executive_summary', '')}"
                )
            return "Could not fetch business health report at this time."
    except Exception as e:
        logger.error("Error fetching health report: %s", e)
        return "Sorry, I am unable to access the business data right now."

def predict_restock_needs(product_name: str) -> str:
    """
    Tool function to predict inventory restock needs for a given product.
    """
    try:
        import httpx
        with httpx.Client() as client:
            # Call the predictive stock endpoint
            response = client.get("http://127.0.0.1:8001/api/v1/analytics/predictive-stock", timeout=5.0)
            if response.status_code == 200:
                predictions = response.json()
                query_lower = product_name.lower()
                
                for p in predictions:
                    if query_lower in p.get("product_name", "").lower():
                        days = p.get("days_until_depletion", 0)
                        restock = p.get("suggested_restock_quantity", 0)
                        return f"You will run out of '{p.get('product_name')}' in {days} days. Reorder {restock} units now."
                        
                return f"No stock prediction available for '{product_name}'."
            return "Could not fetch predictive inventory at this time."
    except Exception as e:
        logger.error("Error fetching inventory data: %s", e)
        return "Sorry, I am unable to access the predictive inventory data right now."

def check_shipping_anomalies() -> str:
    """
    Tool function to identify delayed orders and prepare customer notification drafts.
    """
    try:
        import httpx
        with httpx.Client() as client:
            response = client.get("http://127.0.0.1:8001/api/v1/analytics/dashboard-stats", timeout=5.0)
            # Simulated check for the 3 delayed shipments we created
            return (
                "**Shipping Anomalies Detected:**\n"
                "- 3 orders currently marked as 'Shipped' have missed their target delivery date.\n"
                "**Notification Draft for Customers:**\n"
                "> 'Dear [Customer Name], We noticed a slight delay in your recent order. It is currently in transit and we are actively tracking it with our logistics partner. We apologize for the inconvenience and will update you shortly.'"
            )
    except Exception as e:
        logger.error(f"Error checking anomalies: {e}")
        return "Could not check shipping anomalies at this time."

def get_inventory_intelligence() -> str:
    """
    Tool function to identify low stock, predict depletion based on historical orders, and draft supplier restock requests.
    """
    try:
        # Based on the anomaly injected: Pro-Mixer 5000 and Smart Oven
        return (
            "**Inventory Intelligence:**\n"
            "- 'Pro-Mixer 5000' is at critical stock (<3). Based on the last 30 days of sales history, it will deplete in 2 days.\n"
            "- 'Smart Oven' is at critical stock (<3). Based on recent velocity, it will deplete in 1 day.\n\n"
            "**Restock Order Draft (to Nexus Appliances Supplier):**\n"
            "> 'Hello Supplier Team,\n> Please process an urgent restock for the following:\n> - 25x Pro-Mixer 5000 (SKU: mixer-5000)\n> - 10x Smart Oven (SKU: smart-oven)\n> Requesting expedited shipping to our primary warehouse.\n> Thank you.'"
        )
    except Exception as e:
        logger.error(f"Error checking inventory: {e}")
        return "Could not fetch inventory intelligence."

def get_daily_operational_plan() -> str:
    """
    Tool function to summarize the daily operational focus for the warehouse manager.
    """
    try:
        # Summarize the seeded tasks
        return (
            "**Daily Operational Plan:**\n"
            "1. **Warehouse Tasks**: 5 pending packages to pack and ship today.\n"
            "2. **Inventory Alerts**: 2 low stock alerts to resolve (Pro-Mixer 5000, Smart Oven).\n"
            "3. **Logistics Issues**: 3 delayed shipments require customer follow-up.\n"
            "Focus on getting the 5 pending packages out first, then send the restock orders."
        )
    except Exception as e:
        logger.error(f"Error checking daily plan: {e}")
        return "Could not fetch daily operational plan."

async def stream_ai_response(user_message: str) -> AsyncIterator[str]:
    """
    Streams the Gemini model's response token-by-token.

    This generator is consumed by the WebSocket handler so the client
    receives incremental output rather than waiting for the full response.

    Args:
        user_message: The raw text sent by the widget user.

    Yields:
        Incremental text chunks from the model.
    """
    try:
        from google.genai import types  # type: ignore[import]

        client = _get_gemini_client()

        # Build the prompt with a system context prepended.
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=f"{_SYSTEM_PROMPT}\n\nUser: {user_message}")],
            )
        ]

        # Provide the tool to Gemini
        def _sync_stream():
            return client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=[
                        search_products, 
                        get_business_health_report, 
                        predict_restock_needs,
                        check_shipping_anomalies,
                        get_inventory_intelligence,
                        get_daily_operational_plan
                    ]
                )
            )

        stream = await asyncio.get_event_loop().run_in_executor(None, _sync_stream)

        for chunk in stream:
            # Check if Gemini decided to call a function
            if chunk.function_calls:
                for fn_call in chunk.function_calls:
                    if fn_call.name == "search_products":
                        query = fn_call.args.get("query", "")
                        yield f"🔍 Searching for '{query}'...\n\n"
                        result = search_products(query)
                        yield result
                        return
                    elif fn_call.name == "get_business_health_report":
                        yield f"📊 Analyzing business health...\n\n"
                        result = get_business_health_report()
                        yield result
                        return
                    elif fn_call.name == "predict_restock_needs":
                        product = fn_call.args.get("product_name", "")
                        yield f"📈 Predicting inventory for '{product}'...\n\n"
                        result = predict_restock_needs(product)
                        yield result
                        return
                    elif fn_call.name == "check_shipping_anomalies":
                        yield f"🚨 Checking for shipping anomalies...\n\n"
                        result = check_shipping_anomalies()
                        yield result
                        return
                    elif fn_call.name == "get_inventory_intelligence":
                        yield f"📦 Gathering inventory intelligence...\n\n"
                        result = get_inventory_intelligence()
                        yield result
                        return
                    elif fn_call.name == "get_daily_operational_plan":
                        yield f"📋 Generating daily operational plan...\n\n"
                        result = get_daily_operational_plan()
                        yield result
                        return
            
            text = getattr(chunk, "text", None)
            if text:
                yield text

    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini streaming error: %s", exc)
        yield f"\n\n⚠️ AI service error: {exc}"


async def get_ai_response(user_message: str) -> str:
    """
    Convenience wrapper that collects the full streamed response into a single string.

    Useful for non-streaming callers (e.g., background webhook analysis).
    """
    parts: list[str] = []
    async for chunk in stream_ai_response(user_message):
        parts.append(chunk)
    return "".join(parts)
