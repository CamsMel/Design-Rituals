"""Dépose le deck fini dans le dossier partagé de la tribe.

Compte de service : un robot écrit dans un dossier Drive partagé avec lui. Aucun
écran de consentement pour les consultants, une seule configuration à faire.

Le prix à payer, et il faut le dire à la tribe : le fichier appartient au robot,
pas à son auteur. On compense en préfixant le nom du fichier par le nom du
consultant, et en passant son adresse en description.
"""

from __future__ import annotations

import json
import os
import pathlib

FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")
_RAW_KEY = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

MIME_PPTX = ("application/vnd.openxmlformats-officedocument"
             ".presentationml.presentation")


def enabled() -> bool:
    return bool(FOLDER_ID and _RAW_KEY)


def _service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_info(
        json.loads(_RAW_KEY),
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload(path: pathlib.Path, author_name: str, author_email: str) -> dict:
    """Envoie le fichier et rend son lien. Lève si le Drive n'est pas configuré."""
    if not enabled():
        raise RuntimeError("Drive not configured: set GOOGLE_SERVICE_ACCOUNT_JSON "
                           "and DRIVE_FOLDER_ID")

    from googleapiclient.http import MediaFileUpload

    service = _service()
    meta = {
        "name": f"{author_name} - {path.name}",
        "parents": [FOLDER_ID],
        "description": f"Prepared with the Tribe Design Prep Kit by {author_email}",
    }
    media = MediaFileUpload(str(path), mimetype=MIME_PPTX, resumable=False)
    created = (
        service.files()
        .create(body=meta, media_body=media,
                fields="id,name,webViewLink",
                # Indispensable si le dossier vit dans un Drive partagé plutôt
                # que dans le "Mon Drive" du compte de service.
                supportsAllDrives=True)
        .execute()
    )
    return {"id": created["id"], "name": created["name"],
            "link": created.get("webViewLink")}
