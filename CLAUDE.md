# Notes pour Claude Code

Ce fichier est la mémoire du projet. Lis-le avant de toucher au code.

## Ce qu'est ce repo

Une app web interne à Thiga. Les consultants de la Tribe Design y discutent avec
Claude pour préparer leur rituel hebdomadaire, et récupèrent un `.pptx` à la
charte. Le déroulé complet du déploiement est dans `README.md`, étape par étape.

## Les invariants, à ne pas casser

**La skill fait le métier, pas le backend.** `skill/` contient la vraie skill
`tribe-design-rituals` : 8 templates PPTX à la charte Thiga, deux scripts, et une
fiche par rituel. Ne réimplémente jamais sa logique dans `app/`. Si le
comportement doit changer, il change dans `skill/`.

**Les templates PPTX ne se recréent pas.** Ce sont des exports Google Slides. La
charte vit dans les runs XML. `skill/scripts/fill_deck.py` remplace le texte
dans les runs existants, ce qui est la seule façon de garder la charte intacte.
Ne génère jamais un deck de zéro avec python-pptx.

**Aucun secret dans le repo.** `.gitignore` bloque `.env` et les JSON de compte
de service. Les secrets vivent dans les variables Railway. Une clé commitée reste
dans l'historique : si ça arrive, il faut la révoquer, pas juste supprimer le
fichier.

**`app/static/index.html` est généré**, jamais édité à la main — en théorie.
Découverte le 2026-08-20 : `build_app_page.py` pointe vers
`/home/claude/work/front/build_page.py`, un chemin qui n'existe que dans le
conteneur d'origine où ce code a été écrit. Ce fichier n'est ni dans ce repo ni
ailleurs sur les machines où ce projet a été repris depuis : **le pipeline de
build est cassé**, `python build_app_page.py` échoue avec `FileNotFoundError`.
En attendant de retrouver la source de la V1 (ou de la reconstruire), tout
changement de `app/static/index.html` se fait donc à la main, en miroir exact
des templates `CHAT_SECTION`/`SCRIPT` de `build_app_page.py` pour ne pas les
faire diverger. Le jour où la V1 est retrouvée : corriger le chemin `V1 =` dans
`build_app_page.py`, régénérer, et vérifier par diff que les deux fichiers
racontent la même chose.

**Le texte de l'interface est en anglais, les decks aussi.** Les conversations
avec les consultants suivent leur langue, français en pratique. Pour toute prose
plus longue qu'une puce, les skills `tone-of-voice` puis `anti-ai-writing`
s'appliquent, et elles interdisent notamment le tiret cadratin.

## Faits vérifiés, ne les redécouvre pas

L'API du SDK a été vérifiée par introspection contre `claude-agent-sdk` **0.1.73**
installé. Ces points sont confirmés, pas devinés :

- Le binaire `claude` est embarqué dans le paquet, à
  `claude_agent_sdk/_bundled/claude`. Rien à installer en plus, ni Node, ni CLI.
- `ClaudeAgentOptions` accepte bien : `skills`, `setting_sources`, `plugins`,
  `resume`, `session_id`, `cwd`, `add_dirs`, `allowed_tools`, `permission_mode`,
  `can_use_tool`, `max_turns`, `max_budget_usd`, `include_partial_messages`,
  `env`, `session_store`.
- `include_partial_messages=True` fait arriver des `StreamEvent` dont
  `.event` est l'événement brut de l'API. Le texte au token près se lit dans
  `event["delta"]["text"]` quand `event["type"] == "content_block_delta"`.
- La skill est découverte via `setting_sources=["user"]` et doit donc être à
  `~/.claude/skills/tribe-design-rituals/SKILL.md`. Le `COPY` du Dockerfile la
  pose là. `add_dirs` est nécessaire en plus, sinon lire ses templates depuis le
  dossier de session est refusé.
- `InMemorySessionStore` existe, mais il n'y a **pas** de store S3 ou Redis
  fourni. Ne les invente pas.

## Ce qui n'a jamais tourné pour de vrai

La boucle d'agent n'a jamais été exécutée : le conteneur où ce code a été écrit
n'avait pas de clé API. Ce qui a été testé, navigateur compris : le streaming
SSE, la détection du `.pptx`, le téléchargement, le refus d'écrire hors du
dossier de session, et les boutons de la V1 qui remplissent le chat.

Donc `python smoke_test.py` passe avant toute autre chose. S'il échoue sur le
chargement de la skill, ne contourne pas en réécrivant le prompt système : le
problème est le chemin sur disque.

## Le piège d'ordonnancement

`PUBLIC_BASE_URL` n'existe pas avant le premier déploiement, c'est Railway qui
fabrique le domaine. L'ordre est : déployer sans cette variable, générer le
domaine, puis poser la variable — Railway redéploie tout seul. Pas de piège
Google ici tant qu'il n'y a pas de SSO (voir la section auth ci-dessous) : si
le SSO revient un jour, l'étape "déclarer `<URL>/auth/callback` dans Google
Cloud" refera surface, et sauter cette étape donnera `redirect_uri_mismatch`.

## La clé API : proxy Thiga, pas Anthropic direct

Décision prise le 2026-08-20, à ne pas redécouvrir : l'app route via
`models.thiga.co` (proxy GenAI interne) avec la clé personnelle Slack de
l'utilisateur, pas une clé Anthropic Workspace dédiée. Trois variables :
`ANTHROPIC_BASE_URL=https://models.thiga.co`, `ANTHROPIC_AUTH_TOKEN=sk-...`,
`ANTHROPIC_MODEL=claude-sonnet-5`. Voir `app/agent.py` et le détail du compromis
(budget personnel partagé par une app de prod, `MAX_BUDGET_USD` non garanti avec
un alias de modèle côté proxy) dans le README, étape 1.

## L'auth : aucune, décision assumée le 2026-08-20

Pas de SSO Google (droits Google Cloud manquants), et un mot de passe partagé
posé puis retiré le même jour — assez de friction pour que l'utilisateur
préfère ouvrir l'app à tout le monde en connaissance du risque. `app/auth.py`
ne fait plus rien (`current_user()` retourne toujours un utilisateur
anonyme), et il n'y a plus de middleware dans `app/main.py`.

Conséquence directe : plus de source d'identité côté serveur, donc
`app/agent.py` demande à Claude de récolter le nom du consultant dans la
conversation elle-même (premier tour de questions), et `run_turn`/`_options`
n'ont plus de paramètres `user_name`/`user_email` — ne pas les rajouter en
pensant réparer un oubli, c'est voulu.

**Le compromis assumé, explicitement :** les briefs de mission collés dans le
chat sont accessibles à quiconque a l'URL. Pas de vérification de domaine
`@thiga.co`, pas d'attribution fiable. Si une vraie protection redevient
nécessaire, le SSO Google (implémentation encore dans l'historique git, avant
le commit qui a introduit `APP_PASSWORD`) reste le point de départ le plus
proche ; seul `app/auth.py` (et le middleware à réintroduire dans `main.py`)
changent pour y revenir. `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/
`ALLOWED_EMAIL_DOMAIN`/`APP_PASSWORD` ne sont plus utilisées nulle part dans
le code actuel — ne pas les redécouvrir comme un bug si elles apparaissent
dans un vieux commit.

## Ce que tu ne peux pas faire à ma place

Une chose demande un humain dans un navigateur. Ne tourne pas en rond dessus,
demande-la :

1. Le compte de service Drive, qui demande l'accord de l'IT Thiga.

Le client OAuth Google (étape 1 du README) demande aussi un humain, mais n'est
plus bloquant pour rien : l'app tourne sans lui, voir la section auth ci-dessus.

Tout le reste du `README.md` est automatisable : le repo GitHub, le déploiement,
les variables, le volume, le smoke test, le débogage.
