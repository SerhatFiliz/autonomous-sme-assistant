from __future__ import annotations

from datetime import datetime

AGENT_LOGS: list[dict] = []
WEBHOOK_TRAFFIC: list[dict] = []


class TelemetryService:
    """In-memory telemetry for the demo command center."""

    @staticmethod
    def add_agent_log(agent_name: str, color: str, action: str) -> None:
        AGENT_LOGS.insert(
            0,
            {
                "agent_name": agent_name,
                "color": color,
                "action": action,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        del AGENT_LOGS[50:]

    @staticmethod
    def add_webhook_log(method: str, endpoint: str, payload: str) -> None:
        WEBHOOK_TRAFFIC.insert(
            0,
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "method": method,
                "endpoint": endpoint,
                "payload": payload,
            },
        )
        del WEBHOOK_TRAFFIC[50:]


def add_log(agent_name: str, color: str, action: str) -> None:
    TelemetryService.add_agent_log(agent_name, color, action)


def add_webhook_log(method: str, endpoint: str, payload_str: str) -> None:
    TelemetryService.add_webhook_log(method, endpoint, payload_str)

