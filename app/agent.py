"""Wrapper autour du Claude Agent SDK.

Vérifié contre claude-agent-sdk 0.1.73. Le binaire `claude` est embarqué dans le
paquet Python (`claude_agent_sdk/_bundled/claude`), donc rien à installer en
plus dans l'image.

Le point délicat est la découverte de la skill. Le SDK cherche les skills dans
les emplacements standards, et `setting_sources` dit lesquels lire :

  "user"    -> ~/.claude/skills/<nom>/SKILL.md
  "project" -> <cwd>/.claude/skills/<nom>/SKILL.md

Comme chaque conversation a son propre `cwd` (un dossier de travail jetable où
le deck est écrit), un emplacement "project" obligerait à recopier 6 Mo de
templates par session. On installe donc la skill au niveau "user" dans l'image,
et n'importe quel cwd la voit.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
from typing import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

WORKSPACES = pathlib.Path(os.environ.get("WORKSPACE_ROOT", "/data/sessions"))
MAX_TURNS = int(os.environ.get("MAX_TURNS", "30"))
MAX_BUDGET_USD = float(os.environ.get("MAX_BUDGET_USD", "2.0"))

# Une conversation à la fois par session : deux requêtes qui reprennent la même
# session en parallèle se marchent dessus dans le transcript.
_locks: dict[str, asyncio.Lock] = {}


def workspace(session_id: str) -> pathlib.Path:
    d = WORKSPACES / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _system_prompt(user_name: str, user_email: str) -> str:
    """Ce que l'agent sait du contexte web, en plus de la skill.

    On ne réécrit pas la skill ici. On lui dit seulement où il tourne, qui parle,
    et où déposer le fichier, parce que rien de tout ça n'est déductible.
    """
    return f"""You are running inside the Tribe Design Prep Kit, a small web app
used by Thiga consultants to prepare their weekly ritual. Follow the
tribe-design-rituals skill for everything about the rituals themselves.

Context you cannot infer:
- You are talking to {user_name} ({user_email}). Use that name on the deck cover
  without asking for it.
- Today's working directory is the conversation's own folder. Write the finished
  .pptx there, at the top level, and nowhere else. The app detects it and offers
  it for download, so never tell the consultant to "find the file" somewhere.
- The skill lives at ~/.claude/skills/tribe-design-rituals. Its scripts are at
  ~/.claude/skills/tribe-design-rituals/scripts/. Call them with absolute paths.
- There is no human to approve tool use, and no terminal for the consultant.
  Never ask them to run a command.
- The consultant can drag files into the chat. When they mention an attached
  file, it is already sitting in your working directory under its original
  name — read it directly, never ask where it is or how to access it.

You are in a chat window, so keep messages short. Ask your five questions in one
message, as the skill requires, and don't restate the whole plan before acting.
"""


def _options(session_id: str, user_name: str, user_email: str,
             resume: str | None) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(workspace(session_id)),
        resume=resume,
        # Charge les skills installées au niveau utilisateur dans l'image.
        setting_sources=["user"],
        skills="all",
        # La skill vit hors du cwd : sans ça, lire ses références et ses
        # templates depuis le dossier de session est refusé.
        add_dirs=[str(pathlib.Path.home() / ".claude" / "skills")],
        system_prompt={"type": "preset", "preset": "claude_code",
                       "append": _system_prompt(user_name, user_email)},
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Skill"],
        # Pas d'humain derrière pour arbitrer, mais on garde le garde-fou du
        # handler ci-dessous plutôt que de tout ouvrir.
        permission_mode="acceptEdits",
        can_use_tool=_guard(session_id),
        max_turns=MAX_TURNS,
        max_budget_usd=MAX_BUDGET_USD,
        # Streaming au token près, sinon on n'a le texte qu'en blocs complets.
        include_partial_messages=True,
        # Routé via le proxy GenAI Thiga (models.thiga.co), pas l'API Anthropic
        # directe : ANTHROPIC_AUTH_TOKEN (Bearer) remplace ANTHROPIC_API_KEY.
        env={
            "ANTHROPIC_BASE_URL": os.environ.get("ANTHROPIC_BASE_URL",
                                                  "https://models.thiga.co"),
            "ANTHROPIC_AUTH_TOKEN": os.environ.get("ANTHROPIC_AUTH_TOKEN", ""),
            "ANTHROPIC_MODEL": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
        },
    )


def _guard(session_id: str):
    """Refuse d'écrire ailleurs que dans le dossier de la conversation.

    La skill n'a aucune raison de toucher au reste du conteneur, et une app qui
    reçoit des briefs de mission clients mérite que ce soit vérifié plutôt que
    supposé.
    """
    from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

    root = str(workspace(session_id).resolve())
    skill_dir = str(pathlib.Path.home() / ".claude" / "skills")

    async def handler(tool_name: str, data: dict, context) -> object:
        if tool_name in ("Write", "Edit", "NotebookEdit"):
            path = str(data.get("file_path", ""))
            if not os.path.realpath(path).startswith(root):
                return PermissionResultDeny(
                    message=f"Write outside the conversation folder refused. "
                            f"Write to {root} instead.")
        if tool_name == "Bash":
            cmd = str(data.get("command", ""))
            for forbidden in ("rm -rf /", "curl ", "wget ", "pip install",
                              "npm install", "/etc/", "~/.ssh"):
                if forbidden in cmd:
                    return PermissionResultDeny(
                        message=f"Command refused: {forbidden!r} is not allowed here.")
        return PermissionResultAllow(updated_input=data)

    return handler


def existing_decks(session_id: str) -> list[str]:
    return sorted(p.name for p in workspace(session_id).glob("*.pptx"))


async def run_turn(session_id: str, user_name: str, user_email: str,
                   message: str, resume: str | None) -> AsyncIterator[dict]:
    """Joue un tour et rend des événements prêts à passer en SSE.

    Types émis : `text` (delta), `tool` (nom d'outil, pour l'indicateur
    d'activité), `deck` (un .pptx est apparu), `session` (l'id à réutiliser au
    tour suivant), `done`, `error`.
    """
    lock = _locks.setdefault(session_id, asyncio.Lock())
    if lock.locked():
        yield {"type": "error",
               "message": "Une réponse est déjà en cours dans cette conversation."}
        return

    before = set(existing_decks(session_id))
    sdk_session: str | None = resume

    async with lock:
        try:
            async with ClaudeSDKClient(
                options=_options(session_id, user_name, user_email, resume)
            ) as client:
                await client.query(message)

                async for msg in client.receive_response():
                    if isinstance(msg, StreamEvent):
                        ev = msg.event or {}
                        if ev.get("type") == "content_block_delta":
                            delta = ev.get("delta") or {}
                            if delta.get("type") == "text_delta" and delta.get("text"):
                                yield {"type": "text", "text": delta["text"]}
                        continue

                    if isinstance(msg, SystemMessage):
                        if getattr(msg, "subtype", None) == "init":
                            data = getattr(msg, "data", {}) or {}
                            if data.get("session_id"):
                                sdk_session = data["session_id"]
                            yield {"type": "init",
                                   "skills": data.get("skills"),
                                   "session": sdk_session}
                        continue

                    if isinstance(msg, AssistantMessage):
                        # Filet de sécurité si les deltas ne passent pas : on
                        # n'émet le bloc complet que si rien n'a été streamé.
                        for block in msg.content:
                            if isinstance(block, ToolUseBlock):
                                yield {"type": "tool", "name": block.name}
                        continue

                    if isinstance(msg, ResultMessage):
                        sdk_session = getattr(msg, "session_id", sdk_session) or sdk_session
                        break

        except Exception as exc:  # noqa: BLE001
            yield {"type": "error", "message": f"{type(exc).__name__}: {exc}"}
            return

    for name in sorted(set(existing_decks(session_id)) - before):
        yield {"type": "deck", "name": name}
    yield {"type": "session", "session": sdk_session}
    yield {"type": "done"}
