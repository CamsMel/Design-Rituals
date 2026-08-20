#!/usr/bin/env python3
"""Vérifie que la skill se charge et qu'un deck sort. À lancer AVANT de déployer.

    export ANTHROPIC_AUTH_TOKEN=sk-...   # clé models.thiga.co
    python smoke_test.py

Il n'y a pas de raccourci pour cette étape : si la skill n'est pas découverte,
Claude improvise un deck hors charte et rien dans l'app ne le signalera.
"""
import asyncio, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
os.environ.setdefault("WORKSPACE_ROOT", "/tmp/prepkit-smoke")

from app import agent  # noqa: E402

BRIEF = """Je fais le T'REX de mercredi. Mission chez un assureur mutualiste,
12 000 personnes, 4 designers. Outil interne de déclaration de sinistre, 900
gestionnaires. On m'a demandé de refaire le parcours parce qu'il est moche. En
semaine 2 j'ai vu que les gestionnaires ressaisissaient tout dans un second
outil. J'ai passé deux jours en plateau, fait une carte de parcours, un atelier
de priorisation, un proto du champ auto-rempli. Le chantier d'interconnexion est
passé devant la refonte. Pas de chiffre de gain de temps. Je suis la première
designer de cette équipe.

Ce qui a survécu depuis : la carte de parcours est toujours affichée en salle
plateau, les gestionnaires continuent de s'y référer en réunion. Ce que je
ferais différemment : chiffrer le temps perdu en ressaisie dès la semaine 1 au
lieu d'attendre l'atelier de priorisation. Trois choses à voler pour la tribu :
une carte de parcours convainc un métier mieux qu'un rapport, prototyper le
futur état avant de vendre le chantier, mesurer même approximativement plutôt
que de ne rien chiffrer. Question ouverte pour la tribu : comment on fait
accepter qu'un chantier d'infra passe devant sa propre refonte sans que ça
sonne comme un échec ? Secteur anonymisé, décris juste "a French mutual
insurer, ~12,000 employees". Fais-moi le deck directement avec ça."""


async def main() -> int:
    if not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        print("ANTHROPIC_AUTH_TOKEN manquante (clé models.thiga.co)"); return 2

    saw_skill, text, decks, session = None, [], [], None
    async for ev in agent.run_turn("smoke", "Camille Melin",
                                   "camille.melin@thiga.co", BRIEF, None):
        if ev["type"] == "init":
            saw_skill = ev.get("skills")
            print("skills chargées :", saw_skill)
        elif ev["type"] == "text":
            text.append(ev["text"]); print(ev["text"], end="", flush=True)
        elif ev["type"] == "tool":
            print(f"\n  [outil: {ev['name']}]", flush=True)
        elif ev["type"] == "deck":
            decks.append(ev["name"])
        elif ev["type"] == "session":
            session = ev["session"]
        elif ev["type"] == "error":
            print("\nERREUR:", ev["message"]); return 1

    print("\n" + "=" * 60)
    ws = agent.workspace("smoke")
    ok = True

    if saw_skill and any("tribe-design" in str(s) for s in saw_skill):
        print("OK   la skill tribe-design-rituals est chargée")
    else:
        print(f"ÉCHEC la skill n'apparaît pas dans l'init ({saw_skill!r}).")
        print("     Vérifie que SKILL.md est bien à "
              "~/.claude/skills/tribe-design-rituals/SKILL.md")
        ok = False

    if decks:
        print("OK   deck produit :", ", ".join(decks))
        for name in decks:
            code = os.system(
                f'python "{pathlib.Path.home()}/.claude/skills/tribe-design-rituals'
                f'/scripts/audit_deck.py" "{ws / name}" --ritual trex')
            if code != 0:
                print("     l'audit signale un point bloquant"); ok = False
    else:
        print("ÉCHEC aucun .pptx dans", ws); ok = False

    print("session SDK :", session)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
