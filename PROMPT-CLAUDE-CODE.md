# Le prompt à coller dans Claude Code

Ouvre un terminal dans le dossier `prep-kit`, lance `claude`, et colle ceci.

---

```
Lis CLAUDE.md et README.md avant d'agir.

Objectif : mettre cette app en ligne sur Railway, déployée depuis un repo GitHub
privé de l'organisation Thiga, avec le SSO Google restreint à @thiga.co.

Fais-le dans cet ordre, et arrête-toi pour me demander ce que tu ne peux pas
obtenir toi-même :

1. Installe les dépendances, copie skill/ vers ~/.claude/skills/, et lance
   smoke_test.py. Il te faudra ma clé API : demande-la-moi, ne la mets pas dans
   un fichier suivi par git.
   Si la skill n'apparaît pas dans l'init, corrige le chemin sur disque, ne
   contourne pas en modifiant le prompt système. Ne passe pas à la suite avant
   que le smoke test soit vert.

2. Lance l'app en local avec AUTH_DISABLED=1 et vérifie dans le navigateur
   qu'un message part, que le texte arrive en streaming, et que le .pptx se
   télécharge.

3. Crée le repo GitHub privé et pousse. Vérifie avant de committer qu'aucun
   secret n'est indexé.

4. Déploie sur Railway depuis ce repo. Pose les variables sauf PUBLIC_BASE_URL,
   génère le domaine, puis pose PUBLIC_BASE_URL et monte un volume sur /data.
   Demande-moi le Client ID et le secret Google OAuth.

5. Donne-moi l'URL de callback exacte à déclarer dans Google Cloud, attends que
   je confirme que c'est fait, puis teste la connexion et dis-moi ce que tu vois.

Le Drive vient après, dans un second temps, quand l'IT aura fourni le compte de
service. Ne bloque pas dessus.

À chaque étape, dis-moi ce que tu as vérifié et comment.
```

---

## Ce que Claude Code ne pourra pas faire

Trois choses passent par un navigateur et par toi :

| À obtenir | Où | Remarque |
|---|---|---|
| Clé API Anthropic | platform.claude.com, Workspace → API Keys | affichée une seule fois |
| Client OAuth Google | console.cloud.google.com → Credentials | type "Web application" |
| Compte de service Drive | Google Cloud + accord de l'IT | l'étape la plus longue |

Claude Code peut faire tout le reste : le repo, le déploiement, les variables, le
volume, le smoke test, et le débogage quand ça coince.

## Le premier login Railway

`railway login` ouvre un navigateur. Fais-le toi une fois avant de lancer Claude
Code, il enchaînera ensuite sans friction. Si tu passes par le parcours GitHub
dans l'interface Railway, cette étape ne se pose pas.
