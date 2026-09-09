# MyTradingJournal Pro

Journal de trading dynamique en Django : base de données réelle, comptes
utilisateurs, tableau de bord avec graphiques et calendrier de performance,
et un **coach IA** qui tourne côté serveur pour analyser vos trades par
rapport aux règles de votre stratégie validée (Donchian breakout + filtre
ADX + trailing stop ATR + sortie partielle à 1.5R).

## Installation

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Puis ouvrez http://127.0.0.1:8000

`scikit-learn` (dans `requirements.txt`) est optionnel : le coach IA
fonctionne sans, avec des recommandations 100% basées sur des règles
statistiques. Si scikit-learn est installé et que vous avez 30+ trades, une
couche de régression logistique s'ajoute pour classer les facteurs les plus
corrélés à vos trades gagnants.

## Structure

- `apps/accounts` — inscription, connexion, réinitialisation de mot de passe
- `apps/core` — paramètres utilisateur (devise, solde initial), moteur de
  statistiques partagé (`apps/core/stats.py`)
- `apps/trades` — modèle `Trade`, CRUD, upload de captures d'écran, export CSV
- `apps/dashboard` — tableau de bord (KPIs, courbes, calendrier)
- `apps/analytics` — analyses avancées + coach IA (`apps/analytics/ai.py`)

## Tests

```bash
python manage.py test
```

## Notes

- Base de données SQLite par défaut (fichier `db.sqlite3`). Définissez la
  variable d'environnement `DATABASE_URL` pour basculer sur PostgreSQL sans
  toucher au code (voir `DEPLOY.md`).
- Les emails (réinitialisation de mot de passe) s'affichent dans la console
  du serveur en développement (`EMAIL_BACKEND` console).
- Un compte administrateur est créé automatiquement à la première migration
  s'il n'en existe aucun (voir `apps/core/signals.py`) — identifiants par
  défaut `admin` / `ChangeMoi123!`, personnalisables via les variables
  d'environnement `DJANGO_ADMIN_USERNAME` / `DJANGO_ADMIN_PASSWORD`.
- Pensez à changer `DJANGO_SECRET_KEY` et à définir `DJANGO_DEBUG=False` +
  `DJANGO_ALLOWED_HOSTS` avant tout déploiement en production.

## Déploiement

Voir [DEPLOY.md](DEPLOY.md) pour déployer ce dépôt sur
[Orbit](https://orbit.app.runonflux.io) (build automatique à chaque
`git push`, plan gratuit à vie). Le `Procfile` (`gunicorn`) sert uniquement
à la production sur un hôte Linux — `gunicorn` ne tourne pas sous Windows,
continuez à utiliser `python manage.py runserver` en local.
