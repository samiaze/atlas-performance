# 🔌 Référence API

AtlasPerformance expose une API REST complète construite avec **FastAPI**.

## 📖 Documentation Interactive (Swagger UI)

La méthode recommandée pour explorer l'API est d'utiliser la documentation interactive générée automatiquement.

👉 **Accéder au Swagger** : [http://localhost:8000/docs](http://localhost:8000/docs)

Sur cette interface, vous pouvez :
1.  Voir tous les endpoints disponibles.
2.  Voir les schémas de données (Request/Response).
3.  **Tester l'API** directement depuis le navigateur ("Try it out").

## 🛣️ Principaux Endpoints

L'API est organisée en plusieurs routeurs :

### 🏆 Competitions (`/competitions`)
*   `GET /competitions/` : Lister toutes les compétitions.
*   `GET /competitions/{id}` : Obtenir les détails d'une compétition.

### 🛡️ Teams (`/teams`)
*   `GET /teams/` : Lister les équipes (Supporte pagination et filtrage par compétition).
*   `GET /teams/{id}` : Détails d'une équipe.
*   `GET /teams/{id}/statistics` : Stats agrégées de l'équipe.

### 👤 Players (`/players`)
*   `GET /players/` : Lister les joueurs (Pagination, Recherche).
*   `GET /players/{id}` : Profil complet du joueur.
*   `GET /players/{id}/performance` : Stats moyennes du joueur.

### ⚽ Matches (`/matches`)
*   `GET /matches/` : Calendrier des matchs.
*   `GET /matches/{id}` : Détails (Score, Comps, Events).
*   `GET /matches/{id}/statistics` : Stats comparatives du match.

### 🎭 Performances (`/performances`)
*   `GET /performances/` : Liste des performances brutes (Filtres par joueur, match, note).
*   `GET /performances/{id}` : Détail d'une performance unique.

### 📈 Analytics (`/analytics`)
*   `GET /analytics/dashboard` : Données agrégées pour le dashboard (KPIs, Top Scorers).
*   `GET /analytics/top-scorers` : Classement des buteurs.

---

## 🔐 Authentification
Pour le moment, l'API est ouverte et ne nécessite pas de token d'authentification pour les opérations de lecture (`GET`).
