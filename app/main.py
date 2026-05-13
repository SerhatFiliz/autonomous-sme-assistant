from __future__ import annotations

import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

# ---------------------------------------------------------------------------
# Path fix: allow imports from project root when running from /app/
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel

from ai_agent import chat_with_agent
from database import (
    get_dashboard_metrics,
    get_user_by_username,
    init_db,
    seed_db,
    verify_password,
)

# ---------------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------------

app = FastAPI(title="KOBİ-Agent", version="1.0.0")

# Startup: ensure tables and seed data exist
@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_db()

# ---------------------------------------------------------------------------
# Session / cookie helpers
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "kobi-agent-super-secret-change-me-in-prod")
COOKIE_NAME = "kobi_session"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 hours

_signer = URLSafeTimedSerializer(SECRET_KEY)


def create_session_token(username: str, role: str) -> str:
    return _signer.dumps({"u": username, "r": role})


def decode_session_token(token: str) -> dict | None:
    try:
        data = _signer.loads(token, max_age=SESSION_MAX_AGE)
        return data
    except (BadSignature, SignatureExpired):
        return None


def get_current_user(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return decode_session_token(token)


def require_auth(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"})
    return user


def require_admin(request: Request) -> dict:
    user = require_auth(request)
    if user.get("r") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


# ---------------------------------------------------------------------------
# Jinja2 Templates & static files
# ---------------------------------------------------------------------------

TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
STATIC_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/admin" if user.get("r") == "admin" else "/chat-ui", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    db_user = get_user_by_username(username)
    if not db_user or not verify_password(password, db_user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Kullanıcı adı veya şifre hatalı."},
            status_code=401,
        )

    token = create_session_token(db_user.username, db_user.role)
    redirect_url = "/admin" if db_user.role == "admin" else "/chat-ui"
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.get("r") != "admin":
        return RedirectResponse(url="/chat-ui", status_code=302)

    metrics = get_dashboard_metrics()
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "user": user, "metrics": metrics},
    )


# ---------------------------------------------------------------------------
# Customer Chat UI route
# ---------------------------------------------------------------------------

@app.get("/chat-ui", response_class=HTMLResponse)
def chat_ui(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})


# ---------------------------------------------------------------------------
# API routes (JSON)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat_api(req: ChatRequest, request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum açmanız gerekiyor.")
    answer = chat_with_agent(req.message)
    return {"answer": answer}


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/")
def root():
    return RedirectResponse(url="/login", status_code=302)
