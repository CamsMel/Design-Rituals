"""Google SSO restreint au domaine Thiga.

Deux raisons de ne pas s'en passer : les consultants vont coller des briefs de
mission clients dans cette app, et le nom du consultant sert directement sur la
cover du deck, donc autant le prendre à la source plutôt que de le demander.
"""

from __future__ import annotations

import os

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import RedirectResponse

ALLOWED_DOMAIN = os.environ.get("ALLOWED_EMAIL_DOMAIN", "thiga.co")
BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    client_kwargs={"scope": "openid email profile"},
)

router = APIRouter()

# Permet de tourner en local sans configurer OAuth : `AUTH_DISABLED=1`.
AUTH_DISABLED = os.environ.get("AUTH_DISABLED") == "1"
DEV_USER = {"email": "dev@thiga.co", "name": "Dev Local"}


def current_user(request: Request) -> dict:
    if AUTH_DISABLED:
        return DEV_USER
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="not signed in")
    return user


@router.get("/auth/login")
async def login(request: Request):
    return await oauth.google.authorize_redirect(request, f"{BASE_URL}/auth/callback")


@router.get("/auth/callback")
async def callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        return RedirectResponse("/?error=auth")

    info = token.get("userinfo") or {}
    email = (info.get("email") or "").lower()
    # `hd` est le domaine Google Workspace. On vérifie les deux : le suffixe de
    # l'adresse seul se laisse contourner par un alias.
    domain_ok = info.get("hd") == ALLOWED_DOMAIN or email.endswith(f"@{ALLOWED_DOMAIN}")
    if not (info.get("email_verified") and domain_ok):
        return RedirectResponse("/?error=domain")

    request.session["user"] = {
        "email": email,
        "name": info.get("name") or email.split("@")[0],
    }
    return RedirectResponse("/")


@router.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")


@router.get("/api/me")
async def me(request: Request):
    if AUTH_DISABLED:
        return {"signed_in": True, **DEV_USER}
    user = request.session.get("user")
    return {"signed_in": bool(user), **(user or {})}
