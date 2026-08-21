# Notes pour Claude Code

Ce fichier est la mémoire du projet. Lis-le avant de toucher au code.

## Ce qu'est ce repo

Une app web interne à Thiga. Les consultants de la Tribe Design y discutent avec
Claude pour préparer leur rituel hebdomadaire, et récupèrent un `.pptx` à la
charte. Le déroulé complet du déploiement est dans `README.md`, étape par étape.

## V1 relancée, V2 mise de côté — décision du 2026-08-20

Après les galères Railway (projet supprimé sans prévenir, faute d'abonnement
Thiga) et le blocage Cloud Run (droits GCP manquants), l'utilisateur a choisi
de repartir sur la **V1** pour un premier lancement : une page statique, sans
backend, où chaque consultant copie le prompt de son rituel et le colle dans
son propre Claude (Claude Code en pratique, pour que la skill soit utilisable).
Zéro hébergement à maintenir, zéro clé partagée, zéro auth.

Concrètement :
- Le clic sur "Copy the X prompt" copie de nouveau dans le presse-papiers
  (comportement natif de la V1, jamais supprimé — juste intercepté par le JS
  du chat V2, qui a été débranché). Le chat en drawer et tout le backend
  (`app/`, Railway) restent en place et fonctionnels, juste plus branchés sur
  ces boutons. Pour les rebrancher : revoir le bloc `[data-copy]` dans
  `build_app_page.py`/`index.html` (git blame sur ce commit pour l'ancienne
  version).
- Chaque prompt commence maintenant par une consigne d'auto-installation de
  la skill : cloner `https://github.com/CamsMel/Design-Rituals` (repo rendu
  **public** exprès pour ça, décision explicite de l'utilisateur — "tout doit
  être accessible à la tribe design") et copier `skill/` vers
  `~/.claude/skills/tribe-design-rituals/`. Ça ne marche que dans un Claude
  avec Bash + accès fichiers (Claude Code), pas dans claude.ai en ligne.
- **Piège découvert en éditant ce prompt : il y a deux copies des prompts
  dans `index.html`.** `var PROMPTS` (dans le script natif de la V1, ~ligne
  860) est celle que le clic natif lit réellement. `window.__TG_PROMPTS`
  (injectée par `PROMPT_BRIDGE` dans `build_app_page.py`) n'est qu'un pont
  pour l'ancien override du chat V2, plus lu par personne maintenant que
  l'override est débranché. Éditer la mauvaise copie ne fait rien (piégeant :
  aucune erreur, juste le mauvais texte copié). Les deux ont été mises à jour
  par cohérence, mais seule `PROMPTS` compte tant que le chat reste débranché.
  Aucune des deux n'a de fichier source (la V1 d'origine est introuvable, voir
  plus bas) : toute future modification de ces prompts se fait à la main, aux
  deux endroits.
- **Le rituel est toujours nommé dans le prompt copié** (un bouton par
  rituel) : ça évite la question "quel rituel ?" pour le cas courant. Le
  bouton "Copy the starter prompt" (générique, pour qui ne sait pas encore)
  existe toujours en secours — voir plus bas pour son comportement.
- **Vérifié à froid (HOME vierge, aucune skill installée) : Claude Code
  charge son registre de skills au démarrage de la session.** Un `git clone`
  fait en plein milieu de la conversation n'est donc pas détecté par l'outil
  `Skill` avant une nouvelle session — testé, ça arrive vraiment, pas une
  hypothèse. Le prompt dit donc explicitement de ne pas attendre l'outil
  `Skill` après l'installation, et de lire `SKILL.md` à la main à la place
  (qui indique lui-même quels autres fichiers lire). Sans cette consigne
  explicite, Claude s'en sort quand même en général (testé, il a lu le
  fichier de son propre chef) mais rien ne le garantit à chaque fois — ne pas
  retirer cette phrase du prompt en pensant qu'elle est redondante.
- **La question "quel rituel ?" doit rester seule**, sans rien d'autre dans
  le même message (voir `skill/SKILL.md`, section 1) — testé : sans cette
  précision explicite, Claude a tendance à la fondre avec la date, le
  matériau et une question d'interview dès que le prompt de départ est trop
  minimal, ce qui oblige le consultant à répondre à des choses avant même
  d'avoir vu les questions qui en dépendent.
- **Hébergement bascule sur GitHub Pages le 2026-08-21** (`camsmel.github.io/Design-Rituals`), via `.github/workflows/pages.yml` qui republie `app/static/index.html` à chaque push sur `main`. Railway reste en place mais n'est plus nécessaire pour ce parcours ; les deux peuvent tourner en parallèle sans conflit.
- **Le hero et la section finale ont été refaits le 2026-08-21.** Le CTA
  "Copy the starter prompt" est devenu un sélecteur (`#tg-tdr-picker-btn` +
  menu `#tg-tdr-picker-menu`) : un clic ouvre la liste des 8 rituels, choisir
  l'un d'eux copie directement son prompt (même mécanisme que les boutons
  natifs `[data-copy]`, mais via `data-ritual` pour ne pas entrer en conflit
  avec le handler délégué existant). Le CTA secondaire est renommé "Explore
  all rituals". La section "The starter prompt" (l'ancien prompt générique +
  l'aside de conseils) a été remplacée par une carte "Contribute" qui pointe
  vers le formulaire Notion publié en `.notion.site`. **Notion bloque
  l'iframe pour tout domaine externe** (vérifié via les en-têtes HTTP :
  `X-Frame-Options: SAMEORIGIN` + `frame-ancestors` limité aux domaines
  Notion) — pas une histoire de droits de partage, un lien qui ouvre un
  nouvel onglet est la seule option. Les conseils pratiques de l'ancienne
  aside (langue, où atterrit le fichier, ce qui reste à la main du
  consultant) ont été supprimés avec la section ; une partie recoupait déjà
  "How it works", le reste (le dossier Drive, "what stays with you") n'est
  nulle part ailleurs sur la page pour l'instant.
- **Photos de l'équipe intégrées le 2026-08-21** : deux dans le hero
  (`.tg-tdr__hero-photos`, cachées sous 960px pour ne pas écraser le texte),
  une en clôture de page avant le footer (`.tg-tdr__team-photo`). Redimensionnées
  et compressées avec Pillow/pngquant avant d'inliner en base64 (les fichiers
  reçus faisaient ~1,1 Mo cumulés, les versions inlinées ~235 Ko) — toujours
  garder l'alpha (PNG/WebP, jamais JPEG) : les découpes ovales/arrondies sont
  de la vraie transparence, pas juste une bordure visuelle. Les fichiers
  sources originaux ne sont pas commités (déjà inlinés, inutile de dupliquer).
- **La copy de la page (`index.html`) a été remise à jour le 2026-08-21**
  pour refléter le parcours à 7 étapes de la skill : "How it works" est
  passé à 4 étapes (installation automatique, interview + recherche
  optionnelle, notes de prep à valider, deck), un garde-fou sur les faits
  sourcés a été ajouté, et l'aside "Getting started" qui décrivait encore
  l'ancienne installation manuelle par Camille et un bouton de téléchargement
  a été corrigée. Comme pour les prompts, cette copy vient de la V1
  introuvable : aucun fichier source, tout se modifie à la main dans
  `index.html`.

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
