# saas_ecommerce_ai_agent/core/security.py
# Reusable FastAPI dependency for API key authentication.

from __future__ import annotations

import os

from fastapi import Header, HTTPException, status

# The valid API key is loaded from the environment.
# In production, rotate this key and store it in a secrets manager.
_VALID_API_KEY: str = os.getenv("SAAS_API_KEY", "demo-tenant-key-123")


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-KEY")) -> str:
    """
    FastAPI dependency that validates the `X-API-KEY` request header.

    Raises HTTP 403 if the key is missing or does not match the configured value.
    Returns the validated key on success so downstream handlers can log or route
    by tenant if needed.
    """
    if x_api_key != _VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key.",
        )
    return x_api_key
