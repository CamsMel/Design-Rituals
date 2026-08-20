"""Pas d'authentification.

Décision prise le 2026-08-20 (révisée le même jour) : le mot de passe partagé
introduit assez de friction pour que l'utilisateur préfère ouvrir l'app à
tout le monde, en connaissance du risque — les briefs de mission collés dans
le chat sont accessibles à quiconque a l'URL. Comme il n'y a plus de source
d'identité, Claude demande lui-même le nom du consultant en début de
conversation (voir `agent.py`) plutôt que de le lire d'une session.

Si une vraie protection redevient nécessaire, le SSO Google (voir historique
git, commit qui a introduit `APP_PASSWORD` puis celui du SSO d'origine) est
le point de départ le plus proche : ce fichier est le seul à changer.
"""

from __future__ import annotations

ANONYMOUS_USER = {"email": "", "name": "Tribe consultant"}


def current_user(request) -> dict:
    return ANONYMOUS_USER
