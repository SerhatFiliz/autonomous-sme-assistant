from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.services.telemetry import add_log, add_webhook_log
from core.security import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


class WebhookEvent(BaseModel):
    event_type: str = Field(..., description="E.g. 'order.created', 'stock.low'.")
    store_id: str = Field(..., description="Unique tenant/store identifier.")
    payload: dict[str, Any] = Field(..., description="Arbitrary event-specific data.")


class MessageSentEvent(BaseModel):
    message_id: int
    store_id: str
    sender_email: str | None = None
    content: str


class StoreEventWebhook:
    """Webhook handler for Body-to-Brain event notifications."""

    @staticmethod
    def process(event: WebhookEvent) -> None:
        logger.info("[Webhook] store=%s type=%s payload=%s", event.store_id, event.event_type, event.payload)
        add_log("StoreEventWebhook", "green", f"Received {event.event_type} from {event.store_id}")
        add_webhook_log("POST", "/api/v1/webhooks/store-event", str(event.payload)[:100] + "...")


@router.post("/webhooks/store-event", status_code=202)
async def ingest_event(
    event: WebhookEvent,
    background_tasks: BackgroundTasks,
    _api_key: str = Depends(verify_api_key),
) -> dict[str, str]:
    background_tasks.add_task(StoreEventWebhook.process, event)
    return {"status": "accepted", "event_type": event.event_type, "store_id": event.store_id}


def analyze_message_sentiment(content: str) -> dict[str, Any]:
    lowered = content.lower()
    angry_terms = {
        "angry", "mad", "furious", "terrible", "complaint", "refund", "cancel",
        "kızgın", "kizgin", "berbat", "şikayet", "sikayet", "iade", "iptal",
    }
    urgent_terms = {
        "urgent", "immediately", "asap", "late", "delayed", "lost", "where is",
        "acil", "hemen", "gecikti", "geç kaldı", "kayboldu", "nerede",
    }
    is_angry = any(term in lowered for term in angry_terms)
    is_urgent = any(term in lowered for term in urgent_terms)
    if is_angry and is_urgent:
        sentiment = "Angry/Urgent"
    elif is_angry:
        sentiment = "Angry"
    elif is_urgent:
        sentiment = "Urgent"
    else:
        sentiment = "Neutral"
    return {
        "sentiment": sentiment,
        "is_high_priority": is_angry or is_urgent,
    }


@router.post("/webhooks/message-sent")
async def analyze_message(
    event: MessageSentEvent,
    _api_key: str = Depends(verify_api_key),
) -> dict[str, Any]:
    analysis = analyze_message_sentiment(event.content)
    add_log(
        "MessageSentiment",
        "red" if analysis["is_high_priority"] else "blue",
        f"Message #{event.message_id} for {event.store_id}: {analysis['sentiment']}",
    )
    add_webhook_log("POST", "/api/v1/webhooks/message-sent", event.content[:100] + "...")
    return {
        "status": "analyzed",
        "message_id": event.message_id,
        **analysis,
    }
