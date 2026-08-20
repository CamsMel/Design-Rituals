"""Mot de passe partagé, pas de SSO Google.

Compromis assumé (décidé le 2026-08-20, faute d'accès Google Cloud pour créer
un client OAuth) : un seul secret pour toute la tribu, pas de vérification par
domaine. Le champ "username" du prompt Basic Auth du navigateur sert de nom
affiché sur la cover du deck — rien ne vérifie qu'il dit vrai, contrairement à
l'email d'un compte Google. Si l'accès Google Cloud arrive plus tard, le vrai
SSO (voir historique git) redonne l'identité vérifiée et la restriction de
domaine ; ce fichier est le seul à changer pour y revenir.
"""

from __future__ import annotations

import base64
import binascii
import os
import secrets

from fastapi import APIRouter, HTTPException, Request

APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

router = APIRouter()

# Permet de tourner en local sans mot de passe : `AUTH_DISABLED=1`.
AUTH_DISABLED = os.environ.get("AUTH_DISABLED") == "1"
DEV_USER = {"email": "dev@thiga.co", "name": "Dev Local"}

_UNAUTHORIZED = HTTPException(
    status_code=401,
    detail="not signed in",
    headers={"WWW-Authenticate": 'Basic realm="Tribe Design Prep Kit"'},
)


def _parse_basic_auth(header: str) -> tuple[str, str] | None:
    if not header.startswith("Basic "):
        return None
    try:
        decoded = base64.b64decode(header[6:]).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return None
    if ":" not in decoded:
        return None
    username, _, password = decoded.partition(":")
    return username, password


def current_user(request: Request) -> dict:
    if AUTH_DISABLED:
        return DEV_USER

    parsed = _parse_basic_auth(request.headers.get("authorization", ""))
    if not parsed or not secrets.compare_digest(parsed[1], APP_PASSWORD):
        raise _UNAUTHORIZED

    username = parsed[0].strip() or "Tribe consultant"
    email = username if "@" in username else f"{username}@thiga.co"
    name = username.split("@")[0] if "@" in username else username
    return {"email": email.lower(), "name": name}


@router.get("/api/me")
async def me(request: Request):
    try:
        user = current_user(request)
    except HTTPException:
        return {"signed_in": False}
    return {"signed_in": True, **user}
