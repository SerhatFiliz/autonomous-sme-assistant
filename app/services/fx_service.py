from __future__ import annotations


class FxService:
    """Read-only FX reference service for AI recommendations."""

    def latest_rates(self) -> dict:
        return {
            "base": "USD",
            "rates": {
                "USD": 1.0,
                "EUR": 0.92,
                "TRY": 32.50,
                "GBP": 0.79,
            },
        }

