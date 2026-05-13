# saas_ecommerce_ai_agent/main.py
# Root entry point: `uvicorn main:app --port 8001 --reload`

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import asyncio

from app.services.agent_runner import run_agents_loop

# ---------------------------------------------------------------------------
# Environment & path bootstrap
# ---------------------------------------------------------------------------
load_dotenv()

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Routers (imported after path is set)
# ---------------------------------------------------------------------------
from app.routers.analytics import router as analytics_router # noqa: E402
from app.routers.chat import router as chat_router # noqa: E402
from app.routers.market_intelligence import router as market_router # noqa: E402
from app.routers.recommendations import router as recommendations_router # noqa: E402
from app.routers.webhooks import router as webhooks_router # noqa: E402
from app.routers.nexus_ai import router as nexus_ai_router # noqa: E402

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="KOBİ SaaS AI Brain",
    description="Multi-tenant AI service: webhook ingestion, real-time chat, and Gemini-powered intelligence.",
    version="1.0.0",
)

# Allow all origins so any tenant storefront can reach this SaaS backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the embeddable widget and any other static assets.
STATIC_DIR = ROOT / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(ROOT / "templates"))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_agents_loop())

# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------
app.include_router(webhooks_router, prefix="/api/v1", tags=["Webhooks"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(market_router, prefix="/api/v1", tags=["Market Intelligence"])
app.include_router(recommendations_router, prefix="/api/v1", tags=["Smart Customer Engine"])
app.include_router(nexus_ai_router, prefix="/api/v1", tags=["Nexus AI"])


# ---------------------------------------------------------------------------
# Health check & Dashboard
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health() -> dict:
    """Returns a simple liveness probe response."""
    return {"status": "ok", "service": "KOBİ SaaS AI Brain"}

@app.get("/dashboard", tags=["Dashboard"])
async def saas_dashboard(request: Request):
    """Serves the FastAPI SaaS AI Command Center."""
    # Dummy connected stores for demo
    stores = [
        {"name": "NexusCommerce Demo Store"},
        {"name": "Tech Gadgets Pro"},
        {"name": "Home & Kitchen Essentials"}
    ]
    from app.services.telemetry import AGENT_LOGS, WEBHOOK_TRAFFIC
    return templates.TemplateResponse(request=request, name="saas_dashboard.html", context={"stores": stores, "agent_logs": AGENT_LOGS, "webhook_traffic": WEBHOOK_TRAFFIC})
