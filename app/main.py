"""Tribe Design Prep Kit — API et service des fichiers statiques."""

from __future__ import annotations

import json
import os
import pathlib
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import agent, auth, drive

HERE = pathlib.Path(__file__).parent
STATIC = HERE / "static"

app = FastAPI(title="Tribe Design Prep Kit")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-only-change-me"),
    same_site="lax",
    https_only=os.environ.get("PUBLIC_BASE_URL", "").startswith("https://"),
    max_age=60 * 60 * 12,
)
app.include_router(auth.router)


@app.middleware("http")
async def require_auth(request: Request, call_next):
    """Mot de passe partagé sur tout sauf /healthz (Railway doit pouvoir
    l'appeler sans credentials). Gate aussi la page statique elle-même,
    montée en ASGI brut plus bas, donc pas atteignable par une dépendance
    de route classique."""
    if request.url.path == "/healthz":
        return await call_next(request)
    try:
        auth.current_user(request)
    except HTTPException as exc:
        return Response(status_code=exc.status_code, headers=exc.headers)
    return await call_next(request)


def _session_id(request: Request) -> str:
    """Un dossier de travail par onglet, stable tant que le cookie vit."""
    sid = request.session.get("workspace")
    if not sid:
        sid = uuid.uuid4().hex
        request.session["workspace"] = sid
    return sid


@app.get("/api/config")
async def config(request: Request):
    return {
        "drive_enabled": drive.enabled(),
        "auth_disabled": auth.AUTH_DISABLED,
        "user": auth.current_user(request),
    }


@app.post("/api/chat")
async def chat(request: Request):
    user = auth.current_user(request)
    body = await request.json()
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="empty message")

    sid = _session_id(request)
    resume = request.session.get("sdk_session")

    async def stream():
        # Le SDK renvoie son propre id de session : on le garde pour reprendre
        # la conversation au tour suivant. On ne peut pas écrire dans le cookie
        # pendant un streaming, donc le client nous le renvoie.
        async for event in agent.run_turn(
            sid, user["name"], user["email"], message, resume
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/session")
async def remember_session(request: Request):
    """Le client nous rend l'id de session SDK reçu en fin de stream."""
    auth.current_user(request)
    body = await request.json()
    request.session["sdk_session"] = body.get("session")
    return {"ok": True}


@app.post("/api/reset")
async def reset(request: Request):
    auth.current_user(request)
    request.session.pop("sdk_session", None)
    request.session["workspace"] = uuid.uuid4().hex
    return {"ok": True}


def _deck_path(request: Request, name: str) -> pathlib.Path:
    if "/" in name or "\\" in name or not name.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="bad name")
    path = agent.workspace(_session_id(request)) / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return path


@app.get("/api/deck/{name}")
async def download(request: Request, name: str):
    auth.current_user(request)
    path = _deck_path(request, name)
    return FileResponse(path, filename=name, media_type=drive.MIME_PPTX)


@app.post("/api/drive/{name}")
async def to_drive(request: Request, name: str):
    user = auth.current_user(request)
    path = _deck_path(request, name)
    try:
        return drive.upload(path, user["name"], user["email"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/healthz")
async def healthz():
    return {"ok": True, "drive": drive.enabled()}


# Monté en dernier : la racine sert la page.
app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
