from __future__ import annotations

from app.services.telemetry import add_log


class CustomerSuccessAgent:
    """Personalized order-status messaging owned by the Brain."""

    def notify_order_status(self, order_id: int, customer_email: str, status: str, items: list[dict], customer_name: str | None = None) -> dict:
        customer = customer_name or "there"
        item_names = ", ".join(item.get("name", "item") for item in items) or "your items"
        subject = f"Order #{order_id} is {status.title()}"
        body = f"Hi {customer}, {item_names} are now {status}. We will keep you posted at every step."
        print("--- AI CUSTOMER SUCCESS EMAIL SIMULATION ---")
        print(f"To: {customer_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print("-------------------------------------------")
        add_log("CustomerSuccessAgent", "emerald", f"Sent {status} update for order #{order_id}")
        return {"status": "sent", "subject": subject}
