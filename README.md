# Tribe Design Prep Kit

> **Décision du 2026-08-20 : on relance la V1 pour le premier lancement.**
> Après un projet Railway supprimé sans prévenir (pas d'abonnement Thiga) et
> Cloud Run bloqué (droits GCP manquants), la V2 décrite ci-dessous (chat sur
> la page, backend, hébergement) est mise de côté — pas supprimée, juste
> débranchée. La V1 reprend la main : chaque consultant copie le prompt de
> son rituel et le colle dans son propre Claude Code, qui installe la skill
> lui-même si besoin (le repo est **public** exprès pour ça). Zéro backend à
> maintenir. Détails dans `CLAUDE.md`, section "V1 relancée, V2 mise de côté".
> Le reste de ce fichier documente la V2, utile si on la rebranche un jour.

La V1 envoyait les consultants copier un prompt dans Claude. La V2 (mise de
côté, voir ci-dessus) met le chat sur la page : ils décrivent leur rituel,
Claude les interroge, et le `.pptx` arrive dans la fenêtre avec un bouton vers
le Drive de la tribe.

Les choix arbitrés avec toi : **hébergement Railway**, **dépôt Drive par compte
de service** dans un dossier partagé. Le SSO Google restreint à @thiga.co était
prévu, mais bloqué faute d'accès Google Cloud pour créer le client OAuth (voir
l'étape 1) : l'app tournait avec un **mot de passe partagé**, retiré depuis
(voir CLAUDE.md, section auth).

Compte trois demi-journées si l'IT répond vite. L'étape longue n'est pas le code,
c'est le compte de service Google.

---

## Comment ça marche, en une page

```
navigateur                    conteneur Railway
┌──────────────┐              ┌──────────────────────────────────────┐
│ index.html   │  POST /api/chat  │ FastAPI                          │
│ (page V1 +   │ ───────────────▶ │  ├─ auth.py    mot de passe partagé│
│  chat)       │                  │  ├─ agent.py   Agent SDK         │
│              │ ◀─ SSE ───────── │  │    └─ claude (binaire embarqué)│
│              │  text / tool /   │  │         └─ Bash: fill_deck.py │
│              │  deck / done     │  │              écrit le .pptx   │
│              │                  │  └─ drive.py   compte de service │
└──────────────┘                  └──────────────────────────────────┘
                                     /root/.claude/skills/tribe-design-rituals
                                     /data/sessions/<id>/  ← un dossier par conv.
```

Le point important : **c'est la vraie skill qui tourne**, avec ses 8 templates et
ses deux scripts. L'app ne réimplémente rien du métier. Corriger une fiche de
rituel se fait dans `skill/`, et le comportement change au prochain déploiement.

Le binaire `claude` est embarqué dans le paquet `claude-agent-sdk`. Rien à
installer en plus, ni Node, ni CLI.

---

## Étape 0 — Faire tourner en local, sans rien configurer

Cinq minutes, et ça te dit si le reste vaut la peine.

```bash
cd prep-kit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# la skill à l'endroit où le SDK la cherche
mkdir -p ~/.claude/skills
cp -r skill ~/.claude/skills/tribe-design-rituals

export ANTHROPIC_BASE_URL=https://models.thiga.co
export ANTHROPIC_AUTH_TOKEN=sk-...   # ta clé perso models.thiga.co, reçue par Slack
export ANTHROPIC_MODEL=claude-sonnet-5
python smoke_test.py
```

`smoke_test.py` joue un vrai brief de mission et vérifie deux choses : que la
skill apparaît dans le message d'init, et qu'un `.pptx` sort et passe l'audit.

**Si la skill n'apparaît pas dans l'init, arrête-toi là.** Claude improviserait
un deck hors charte et rien dans l'app ne te le dirait. Vérifie que
`~/.claude/skills/tribe-design-rituals/SKILL.md` existe bien à ce chemin exact.

Puis l'app, sans SSO :

```bash
AUTH_DISABLED=1 SESSION_SECRET=dev WORKSPACE_ROOT=/tmp/ws \
  uvicorn app.main:app --reload
```

Sur `http://localhost:8000`, tu dois pouvoir cliquer "Prepare my T'REX 🦖",
envoyer, voir le texte arriver au fil de l'eau, et récupérer le fichier.

---

## Étape 1 — La clé, puis l'accès

### La clé : proxy GenAI Thiga, pas l'API Anthropic directe

**Choix arbitré, à relire si tu reprends ce projet plus tard.** Ce projet n'utilise
pas de clé Anthropic Workspace dédiée. Il route via `models.thiga.co`, le proxy
GenAI interne, avec la clé personnelle reçue par message privé Slack au moment de
l'onboarding (voir `utiliser-la-plateforme-genai.md`, section 4). Trois variables,
pas une :

```
ANTHROPIC_BASE_URL=https://models.thiga.co
ANTHROPIC_AUTH_TOKEN=sk-...     # la clé perso, en Bearer token, pas en x-api-key
ANTHROPIC_MODEL=claude-sonnet-5 # nom du modèle côté proxy, pas l'id Anthropic natif
```

**Le compromis assumé, explicitement :** cette clé est personnelle, liée à un tier
et un budget mensuel individuel (5 à 200 $ selon le tier). L'app de prod tourne
donc sur le quota d'une seule personne. Si cette personne quitte Thiga, change de
tier, ou que l'usage cumulé des consultants dépasse son budget perso, l'app tombe
— et la facture n'est pas attribuée à un budget "Tribe Design" mais à un individu.
C'est l'inverse de ce qu'une clé Workspace dédiée aurait donné (attribution claire,
limite de dépense propre au projet, révocable sans casser d'autres usages). Si ce
compromis devient un problème, la bascule vers une vraie clé Anthropic Workspace
(platform.claude.com, Organization Admin, limite de dépense dédiée) ne touche que
`app/agent.py` et ces trois variables.

**Le garde-fou `MAX_BUDGET_USD` n'est pas garanti ici.** Il repose sur le calcul de
coût interne du binaire `claude`, qui doit reconnaître le nom de modèle pour lui
associer un tarif. `claude-sonnet-5` est un alias côté proxy, pas l'identifiant
Anthropic natif : si le binaire ne le reconnaît pas, le budget par tour n'est pas
appliqué et seul le tier du proxy (5 à 200 $/mois) protège de la facture. Pas
vérifié en conditions réelles — à surveiller aux premiers essais.

Si tu veux malgré tout la clé Workspace dédiée d'origine : ouvre
**[platform.claude.com](https://platform.claude.com)** → **Workspace** → **API
Keys** → crée la clé (affichée une seule fois, **Organization Admin** requis) →
pose une limite de dépense sur le Workspace. Ne réutilise jamais une clé partagée
entre projets : elle ne se révoque pas sans casser les autres usages, et la
dépense n'est plus attribuable.

### L'écran OAuth Google — bloqué, et l'app tourne sans authentification

Décision prise le 2026-08-20, révisée le même jour : la personne qui a lancé
ce déploiement n'avait pas les droits pour créer un client OAuth dans Google
Cloud Console (pas Owner/Editor sur le projet GCP Thiga). Un mot de passe
partagé (HTTP Basic Auth) a d'abord remplacé le SSO, puis a été retiré à son
tour — assez de friction pour préférer ouvrir l'app à tout le monde plutôt que
de la garder derrière un secret. `app/auth.py` ne fait donc plus rien.

**Le compromis assumé, explicitement :** l'app est publique. Les briefs de
mission collés dans le chat sont accessibles à quiconque a l'URL. Comme il n'y
a plus aucune source d'identité, Claude demande lui-même le nom du consultant
en début de conversation (voir `agent.py`) plutôt que de le lire d'une
session. Si une vraie protection redevient nécessaire — le SSO Google
(implémentation encore dans l'historique git) reste le point de départ le
plus proche ; seul `app/auth.py` change pour y revenir.

Teste en local avant de déployer :

```bash
export PUBLIC_BASE_URL=http://localhost:8000
export SESSION_SECRET=$(openssl rand -hex 32)
uvicorn app.main:app --reload
```

---

## Étape 2 — Déployer, depuis GitHub

### L'ordre compte, et il n'est pas intuitif

L'URL n'existe pas encore. C'est Railway qui la fabrique, après le premier
déploiement. Donc :

```
1. push du repo sur GitHub          (repo PRIVÉ)
2. Railway → New Project → GitHub repo
3. poser les variables SAUF PUBLIC_BASE_URL
4. Deploy  → ça démarre
5. Settings → Generate Domain  → l'URL apparaît enfin
6. poser PUBLIC_BASE_URL = cette URL → Railway redéploie tout seul
7. ouvrir l'URL — accès direct, sans mot de passe
```

Pas de piège d'ordonnancement Google ici. Si le vrai SSO revient un jour,
l'étape "déclarer l'URL dans Google Cloud" refera surface (voir l'étape 1).

### Le push

```bash
cd prep-kit
git init && git add . && git commit -m "Tribe Design Prep Kit"
gh repo create thiga-co/tribe-design-prep-kit --private --source=. --push
```

Le `.gitignore` du repo exclut déjà `.env` et tout fichier ressemblant à une clé
de compte de service. **Aucun secret ne va dans le repo**, même privé : ils vivent
dans les variables Railway. Une clé commitée reste dans l'historique même après
suppression du fichier, et il faut la révoquer.

Si tu n'as pas encore accès à l'org GitHub `thiga-co` (invitation à demander sur
Slack **#help-genai-platform**), pousse d'abord sous ton compte perso en privé,
puis transfère l'ownership vers `thiga-co` une fois l'accès obtenu — ça ne casse
pas l'historique.

### Le déploiement

Dans [railway.com](https://railway.com) : **New Project → Deploy from GitHub
repo →** choisis le repo. Railway voit le `Dockerfile` et construit avec.

Avant de cliquer Deploy, **Add variables** :

| Variable | Valeur |
|---|---|
| `ANTHROPIC_BASE_URL` | `https://models.thiga.co` |
| `ANTHROPIC_AUTH_TOKEN` | la clé perso de l'étape 1, reçue par Slack |
| `ANTHROPIC_MODEL` | `claude-sonnet-5` |
| `SESSION_SECRET` | `openssl rand -hex 32` |
| `MAX_TURNS` | `30` |
| `MAX_BUDGET_USD` | `2.0` |

Puis **Settings → Networking → Generate Domain**, et seulement là :

| Variable | Valeur |
|---|---|
| `PUBLIC_BASE_URL` | `https://<le-domaine-généré>` |

Ajoute enfin un **volume monté sur `/data`** (Settings → Volumes). Sans lui, les
dossiers de conversation partent à chaque redéploiement, et le lien de
téléchargement d'un deck préparé la veille casse.

Chaque push sur `main` redéploie tout seul. Pour ne pas déployer en cassant,
travaille sur une branche et passe par une pull request.

Vérifie : `curl https://<ton-domaine>/healthz` doit répondre `{"ok":true,...}`.

### Si tu préfères la ligne de commande

```bash
npm i -g @railway/cli
railway login
railway init
railway up
railway domain
railway variables --set ANTHROPIC_BASE_URL=https://models.thiga.co --set ANTHROPIC_AUTH_TOKEN=sk-... --set ANTHROPIC_MODEL=claude-sonnet-5 --set ...
```

Même ordre, mêmes pièges. Le parcours GitHub a l'avantage de redéployer sur push,
ce qui compte dès que vous êtes deux à toucher au code.

## Étape 3 — Le Drive

C'est l'étape qui dépend de quelqu'un d'autre. Commence-la en parallèle de
l'étape 1 plutôt qu'après.

**Ce qu'il faut demander à l'IT**, formulé pour qu'ils puissent dire oui :

> Un compte de service Google Workspace, sans délégation domain-wide, avec la
> Drive API activée sur son projet. Je partage un seul dossier Drive avec son
> adresse en droit Éditeur. Il n'aura accès à rien d'autre : le scope demandé est
> `drive.file`, qui ne donne accès qu'aux fichiers créés par le compte lui-même.

Ensuite :

1. Google Cloud → **IAM & Admin → Service Accounts → Create**. Pas de rôle IAM.
2. Onglet **Keys → Add key → JSON**. Tu récupères un fichier.
3. **APIs & Services → Enable APIs → Google Drive API.**
4. Dans Drive, sur le dossier `Tribe Design / Rituals`, **Partager** avec
   l'adresse du compte de service (`...@....iam.gserviceaccount.com`), en
   **Éditeur**.
5. Prends l'ID du dossier dans son URL, après `/folders/`.

```bash
railway variables \
  --set DRIVE_FOLDER_ID=1AbC... \
  --set GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account.json | jq -c .)"
```

Le `jq -c` met le JSON sur une seule ligne. Sans ça, la variable est tronquée au
premier saut de ligne et l'erreur est illisible.

Le bouton "Send to the tribe Drive" apparaît tout seul quand ces deux variables
sont posées. Sans elles, seul le téléchargement est proposé, et l'app fonctionne.

**À dire à la tribe** : le fichier appartient au compte de service, pas à son
auteur. Le nom du consultant est préfixé au nom du fichier et son adresse est en
description, mais dans la colonne "Propriétaire" du Drive, il y aura un robot. Si
c'est bloquant, on bascule sur OAuth par consultant, ce qui ajoute un écran de
consentement et un refresh token à stocker par personne.

---

## Étape 4 — Mettre la page à jour

Le HTML servi est `app/static/index.html`. Il est **généré**, pas édité à la main :

```bash
python build_app_page.py
```

Le script charge le générateur de la V1 (`../front/build_page.py`), récupère son
HTML, et y injecte le CSS, le markup et le JS du chat. Une correction de copy ou
un neuvième rituel ajouté dans `build_page.py` se retrouve donc dans les deux
versions, sans recopie.

En V2, les boutons de la V1 changent de comportement tout seuls : "Copy the T'REX
prompt" devient "Prepare my T'REX" et remplit la boîte de chat au lieu du
presse-papiers.

---

## Ce que ça coûte

| Poste | Estimation |
|---|---|
| Railway (1 service, volume) | 5 à 20 $ / mois |
| API Anthropic, par deck préparé | 0,30 à 1,00 $ selon la longueur du brief |
| 40 consultants, un rituel par semaine | 4 decks par mois, donc quelques dollars |

Le vrai risque de facture n'est pas le volume, c'est une conversation qui part en
boucle. Deux garde-fous sont déjà posés : `MAX_TURNS=30` et `MAX_BUDGET_USD=2.0`
par tour. Baisse-les si tu veux dormir tranquille, remonte-les si un
Let's Work(shop) se fait couper au milieu.

---

## Ce qui est vérifié, et ce qui ne l'est pas

**Vérifié ici, navigateur compris** : le streaming SSE token par token, la
détection du `.pptx` produit, le téléchargement (fichier valide, 5 slides), le
refus de sortir du dossier de session, les boutons de la V1 qui remplissent le
chat, l'API du SDK contre la version 0.1.73 installée.

**Pas vérifié, parce que ce conteneur n'a pas de clé API** : la boucle d'agent
elle-même, donc le chargement effectif de la skill et la production d'un deck par
Claude. C'est exactement ce que `smoke_test.py` couvre, et c'est pour ça que
l'étape 0 passe avant tout le reste.

**Pas vérifié non plus** : le SSO contre un vrai tenant Google, et l'envoi Drive
contre un vrai compte de service. Les deux se testent en dix minutes une fois les
identifiants en main.

---

## Les pièges, dans l'ordre où ils arrivent

1. **La skill n'est pas trouvée.** Le SDK cherche `SKILL.md` sous
   `~/.claude/skills/<nom>/`. Dans l'image, le `COPY` du Dockerfile le pose là.
   En local, c'est le `cp -r` de l'étape 0. Le message d'init liste les skills
   chargées : c'est le seul contrôle qui compte.
2. **Le JSON du compte de service tronqué.** Passe-le par `jq -c`.
3. **Les decks qui disparaissent.** Monte un volume sur `/data`.
4. **Deux messages envoyés en même temps.** Un verrou par session les met en
   file plutôt que de laisser deux tours écrire dans le même transcript.
5. **Le SSE coupé par un proxy.** L'en-tête `X-Accel-Buffering: no` est déjà
   posé ; si tu passes derrière un autre reverse proxy, désactive son buffering.

---

## Fichiers

| Fichier | Rôle |
|---|---|
| `app/main.py` | routes, cookie de session, téléchargement, garde anti-traversée |
| `app/agent.py` | options du SDK, streaming, verrou par session, garde sur les écritures |
| `app/auth.py` | aucune auth ; identité recueillie par Claude dans la conversation |
| `app/drive.py` | dépôt par compte de service, désactivé proprement si non configuré |
| `app/static/index.html` | **généré** par `build_app_page.py` |
| `skill/` | copie de la skill, embarquée dans l'image |
| `smoke_test.py` | le test à passer avant de déployer |
