from __future__ import annotations

import asyncio

from app.agents.pricing_strategy import PricingStrategyAgent
from app.agents.supply_chain import SupplyChainAgent
from app.services.telemetry import AGENT_LOGS, WEBHOOK_TRAFFIC, add_log, add_webhook_log


async def run_agents_loop() -> None:
    """Run non-transactional intelligence checks in the background."""
    supply_chain_agent = SupplyChainAgent()
    pricing_agent = PricingStrategyAgent()
    while True:
        await supply_chain_agent.run_background_check()
        await asyncio.sleep(2)
        await pricing_agent.run_background_check()
        await asyncio.sleep(60)

