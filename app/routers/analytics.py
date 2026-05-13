from __future__ import annotations

import random
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.supply_chain import SupplyChainAgent
from app.services.fx_service import FxService
from database import Order, Product, get_session

router = APIRouter()


class StockPrediction(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    days_until_depletion: int
    suggested_restock_quantity: int
    optimal_purchase_price: float


class FinanceSummary(BaseModel):
    daily_revenue: float
    weekly_revenue: float
    monthly_revenue: float
    profit_loss: float
    expenses: float
    executive_summary: str


@router.get("/predictive-stock", response_model=List[StockPrediction])
def get_predictive_stock(session: Session = Depends(get_session)):
    products = session.scalars(select(Product)).all()
    return [prediction.__dict__ for prediction in SupplyChainAgent().predict_stock(products)]


@router.get("/finance", response_model=FinanceSummary)
def get_finance_summary(session: Session = Depends(get_session)):
    today = date.today()
    orders = session.scalars(select(Order)).all()
    daily_rev = weekly_rev = monthly_rev = 0.0
    for order in orders:
        if order.order_date == today:
            daily_rev += order.product.price
        if today - order.order_date <= timedelta(days=7):
            weekly_rev += order.product.price
        if today - order.order_date <= timedelta(days=30):
            monthly_rev += order.product.price
    expenses = monthly_rev * 0.4
    profit_loss = monthly_rev - expenses
    summary = "Executive Summary: Business is highly profitable." if profit_loss > 1000 else "Executive Summary: Margins are tight."
    return FinanceSummary(
        daily_revenue=round(daily_rev, 2),
        weekly_revenue=round(weekly_rev, 2),
        monthly_revenue=round(monthly_rev, 2),
        profit_loss=round(profit_loss, 2),
        expenses=round(expenses, 2),
        executive_summary=summary,
    )


@router.get("/currency")
def get_live_currency():
    return FxService().latest_rates()


@router.get("/recommendation")
def get_recommendation(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    products = session.scalars(select(Product).where(Product.id != product_id)).all()
    related = random.sample(list(products), min(2, len(products))) if products else []
    return {"product_id": product_id, "recommendations": [{"id": item.id, "name": item.name, "price": item.price} for item in related]}


@router.get("/dashboard-stats")
def get_dashboard_stats():
    return {
        "total_revenue": 0,
        "pending_orders": 0,
        "growth_rate": 0,
        "top_categories": [],
        "source": "Brain telemetry only; primary sales BI is owned by Django Body.",
    }


@router.get("/sales-charts")
def get_sales_charts():
    return {"dates": [], "revenues": [], "source": "Django Body owns primary sales transactions."}
