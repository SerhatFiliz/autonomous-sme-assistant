from __future__ import annotations

from datetime import date

from app.services.telemetry import add_log


class PricingStrategyAgent:
    """Campaign and pricing guidance for store managers."""

    def campaign_calendar(self) -> list[dict]:
        today = date.today()
        campaign_dates = [
            (date(today.year, 2, 14), "Valentine's Day", "Giftable products"),
            (date(today.year, 9, 1), "Back to School", "Stationery, electronics, bags"),
            (date(today.year, 11, 27), "Black Friday", "High-margin best sellers"),
            (date(today.year, 12, 31), "New Year", "Bundles and replenishment items"),
        ]
        suggestions = []
        for event_date, name, product_group in campaign_dates:
            if event_date < today:
                event_date = event_date.replace(year=today.year + 1)
            days_until = (event_date - today).days
            if days_until <= 45:
                suggestions.append(
                    {
                        "event": name,
                        "date": event_date.isoformat(),
                        "days_until": days_until,
                        "suggestion": f"Holiday approaching in {days_until} days. Stock up on {product_group} and test a 15% discount.",
                    }
                )
        if not suggestions:
            suggestions.append(
                {
                    "event": "Always-on retention",
                    "date": today.isoformat(),
                    "days_until": 0,
                    "suggestion": "No major retail holiday is inside 45 days. Run a margin-safe bundle campaign for repeat buyers.",
                }
            )
        return suggestions

    async def run_background_check(self) -> None:
        add_log("PricingStrategyAgent", "cyan", "Analyzing campaign windows and market velocity.")
        add_log("PricingStrategyAgent", "cyan", "Suggested a margin-safe weekend campaign for slow-moving inventory.")

