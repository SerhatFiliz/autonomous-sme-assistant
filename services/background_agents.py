"""Compatibility wrapper for the new app.services/app.agents structure."""

from app.services.agent_runner import run_agents_loop
from app.services.telemetry import AGENT_LOGS, WEBHOOK_TRAFFIC, add_log, add_webhook_log

