# Déploiement — GitHub + Orbit (Flux)

Ce dépôt est prêt à être déployé tel quel sur [Orbit](https://orbit.app.runonflux.io) (build Nixpacks sans Dockerfile) via un simple `git push`. Ce document explique les étapes **à faire vous-même** — la création de compte sur une plateforme tierce et l'autorisation d'accès à votre dépôt GitHub sont des actions que je ne peux pas effectuer à votre place.

## 1. Pousser le code sur GitHub

Une fois le dépôt GitHub créé et le code poussé (voir le reste de la conversation), votre code est visible sur GitHub — c'est la partie "hébergement du code source".

## 2. Créer votre compte Orbit et connecter le dépôt

1. Allez sur https://orbit.app.runonflux.io/dashboard/deploy
2. Créez un compte (email, ou connexion via GitHub).
3. Collez l'URL de votre dépôt GitHub. Orbit détecte automatiquement qu'il s'agit d'un projet Python/Django.
4. Choisissez le plan **Free forever** (0.5 CPU, 1 Go RAM, 5 Go stockage, 1 instance).
   - ⚠️ Le plan gratuit ne fonctionne qu'avec un dépôt **public**. Un dépôt privé passe automatiquement en offre "Enterprise" (+1,33 $/mois).

## 3. Variables d'environnement à définir dans Orbit

Dans le tableau de bord Orbit, section "Environment Variables" de votre app, ajoutez :

| Variable | Valeur |
|---|---|
| `DJANGO_SECRET_KEY` | Une valeur longue et aléatoire (ex. générée avec `python -c "import secrets; print(secrets.token_urlsafe(50))"`) — **ne réutilisez pas** la clé de développement présente dans `settings.py` |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | le domaine fourni par Orbit, ex. `votre-app.runonflux.io` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://votre-app.runonflux.io` |
| `DJANGO_ADMIN_PASSWORD` | (optionnel) un mot de passe admin de votre choix — sinon la valeur par défaut `ChangeMoi123!` est utilisée au premier démarrage, **changez-la** dans ce cas dès la première connexion |

## 4. Stockage : la base SQLite ne survit pas forcément à un redéploiement

Le plan gratuit tourne sur une seule instance dont le disque n'est pas garanti persistant d'un déploiement à l'autre. Deux options :

- **Acceptable pour démarrer/tester** : ne rien changer, la base SQLite se recrée vide (avec le compte admin auto-créé) à chaque nouveau déploiement.
- **Recommandé pour un usage réel** : brancher une base Postgres externe gratuite (ex. [Neon](https://neon.tech) ou [Supabase](https://supabase.com), toutes deux avec un plan gratuit), et définir la variable d'environnement `DATABASE_URL` (ex. `postgres://user:password@host/dbname`) dans Orbit — le projet la détecte automatiquement (`dj_database_url`) et bascule dessus.

## 5. Déployer

Cliquez sur "Deploy". Orbit construit l'image (installe `requirements.txt`, exécute la commande du `Procfile` : migrations + fichiers statiques + démarrage de `gunicorn`), puis votre site est en ligne.

## 6. Déploiement automatique à chaque `git push`

C'est déjà actif par défaut une fois le dépôt connecté : chaque `git push` sur la branche par défaut déclenche un webhook GitHub → nouveau build → nouveau déploiement automatique chez Orbit. Rien d'autre à configurer.

## Ce qui a déjà été préparé dans le code pour ce déploiement

- [Procfile](Procfile) — commande de démarrage (migrations + collectstatic + gunicorn).
- [requirements.txt](requirements.txt) — `gunicorn`, `whitenoise` (sert les fichiers statiques sans serveur séparé), `dj-database-url`.
- [trading_journal/settings.py](trading_journal/settings.py) — lit `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_URL` depuis l'environnement ; active automatiquement HTTPS/cookies sécurisés/HSTS dès que `DJANGO_DEBUG=False`.
- Le compte admin est créé automatiquement au premier `migrate` (voir [apps/core/signals.py](apps/core/signals.py)) — pas besoin de `createsuperuser` en SSH.
