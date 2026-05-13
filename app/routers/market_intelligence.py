from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agents.customer_success import CustomerSuccessAgent
from app.agents.market_intelligence import MarketIntelligenceAgent
from app.agents.pricing_strategy import PricingStrategyAgent

router = APIRouter()


class MarketIntelligenceRequest(BaseModel):
    product_name: str
    cost_price: float = Field(0, ge=0)
    target_profit_margin: float = Field(30, ge=0, le=95)
    currency: str = "TRY"


class OrderWorkflowEvent(BaseModel):
    order_id: int
    customer_email: str
    customer_name: str | None = None
    status: str
    items: list[dict] = []


@router.post("/market-intelligence-agent")
async def market_intelligence_agent(payload: MarketIntelligenceRequest):
    return await MarketIntelligenceAgent().analyze(
        product_name=payload.product_name,
        cost_price=payload.cost_price,
        target_profit_margin=payload.target_profit_margin,
        currency=payload.currency,
    )


@router.get("/strategy-calendar")
async def strategy_calendar():
    return {"suggestions": PricingStrategyAgent().campaign_calendar()}


@router.post("/order-workflow/notify")
async def order_workflow_notify(event: OrderWorkflowEvent):
    return CustomerSuccessAgent().notify_order_status(
        order_id=event.order_id,
        customer_email=event.customer_email,
        customer_name=event.customer_name,
        status=event.status,
        items=event.items,
    )

