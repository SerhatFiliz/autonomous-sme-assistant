from __future__ import annotations

import os
from typing import Any, Callable

from dotenv import load_dotenv

from database import check_critical_stock, get_order_status, get_product_info

SYSTEM_PROMPT = (
    "Sen KOBİ'ler için geliştirilmiş otonom bir asistansın. "
    "Müşteri veya yöneticilerden gelen talepleri anla, elindeki fonksiyonları kullanarak "
    "veri tabanından gerçek bilgileri çek ve kullanıcıya doğal, kibar bir dille yanıt ver."
)


def _missing_key_message() -> str:
    return (
        "Gemini API anahtarı bulunamadı. Lütfen `GEMINI_API_KEY` ortam değişkenini ayarlayın "
        "(veya `.env` dosyasına ekleyin), ardından tekrar deneyin."
    )


def _run_with_google_genai(user_message: str) -> str:
    # Newer SDK: `google-genai`
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _missing_key_message()

    client = genai.Client(api_key=api_key)

    tools: list[Callable[..., Any]] = [
        get_order_status,
        check_critical_stock,
        get_product_info,
    ]

    cfg = types.GenerateContentConfig(
        tools=tools,
        # If the SDK version doesn't support this field, the except below will handle it.
        system_instruction=SYSTEM_PROMPT,  # type: ignore[arg-type]
    )

    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=cfg,
        )
        return (resp.text or "").strip() or "Yanıt üretilemedi."
    except TypeError:
        # Backward compatible: provide system prompt as a system content instead.
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(
                    role="system",
                    parts=[types.Part.from_text(text=SYSTEM_PROMPT)],
                ),
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                ),
            ],
            config=types.GenerateContentConfig(tools=tools),
        )
        return (resp.text or "").strip() or "Yanıt üretilemedi."


def _run_with_google_generativeai(user_message: str) -> str:
    # Legacy SDK: `google-generativeai`
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _missing_key_message()

    genai.configure(api_key=api_key)

    # This SDK's tool/function calling surface is less stable across versions.
    # We still provide a useful fallback: the model answers, and we keep tools for future extension.
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )
    resp = model.generate_content(user_message)
    return (getattr(resp, "text", "") or "").strip() or "Yanıt üretilemedi."


def chat_with_agent(user_message: str) -> str:
    """
    Kullanıcının mesajını alır, uygun aracı (function calling) çalıştırarak yanıt döner.

    Not: `google-genai` varsa otomatik function calling ile DB fonksiyonlarını çağırır.
    Aksi halde `google-generativeai` ile temel yanıt üretir.
    """
    load_dotenv()

    try:
        return _run_with_google_genai(user_message)
    except Exception:
        # Son çare fallback (ör. google-genai kurulu değilse)
        return _run_with_google_generativeai(user_message)

