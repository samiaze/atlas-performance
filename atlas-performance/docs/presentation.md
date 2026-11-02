# Présentation Détaillée : Atlas Performance Analytics

---

**Réalisé par :**
- **ABBA Badreddine**
- **ZENBILE Samia**
- **RAJI Khouloud**
- **BOUDALI Ilham**

**Encadré par :**
- **Mr Z. CHIBA**

**Année Universitaire :** 2025/2026

---

## Table des Matières

1. [Introduction Générale](#1-introduction-générale)
2. [Architecture du Système](#2-architecture-du-système)
3. [Pipeline ETL & Ingénierie des Données](#3-pipeline-etl--ingénierie-des-données)
4. [Conception de la Base de Données](#4-conception-de-la-base-de-données)
5. [Développement Backend](#5-développement-backend)
6. [Interface Utilisateur (UI/UX)](#6-interface-utilisateur-uiux)
7. [Fonctionnalités Détaillées](#7-fonctionnalités-détaillées)
8. [Technologies & Outils](#8-technologies--outils)
9. [Bilan & Perspectives](#9-bilan--perspectives)

---

## 1. Introduction Générale

### 1.1 Contexte du Projet

Le football moderne a connu une transformation radicale grâce à l'adoption massive de l'analyse de données. Les clubs professionnels investissent désormais des millions dans des départements d'analytics qui influencent directement les décisions tactiques, les recrutements et la gestion de la performance.

**Évolution de l'Analytics Football :**
- **Années 2000** : Statistiques basiques (buts, passes, possessions)
- **Années 2010** : Introduction des Expected Goals (xG), passing networks
- **Années 2020** : Machine Learning, tracking data, analytics prédictifs

**Problématiques identifiées :**
- Les données sont dispersées sur plusieurs plateformes
- Les outils professionnels (Wyscout, Opta) sont extrêmement coûteux
- Manque d'outils accessibles pour les clubs semi-professionnels
- Difficulté d'interprétation des données brutes pour les non-spécialistes

### 1.2 Objectifs du Projet

**Objectif Principal :**
Développer une plateforme Web Full-Stack permettant l'analyse complète des performances footballistiques à travers une interface moderne et intuitive.

**Objectifs Spécifiques :**
1. **Centralisation** : Regrouper toutes les données de matchs en une seule base
2. **Analytics Avancés** : Calculer des métriques professionnelles (GPI, xG, Pass Accuracy)
3. **Visualisation** : Créer des dashboards interactifs de niveau broadcast
4. **Accessibilité** : Interface responsive et rapide
5. **Extensibilité** : Architecture modulaire permettant l'ajout de nouvelles fonctionnalités

### 1.3 Périmètre Fonctionnel

**Dans le Scope :**
- Gestion multi-compétitions
- Suivi de performances individuelles et collectives
- Tableaux de bord analytiques
- Export de données (CSV)
- Filtrage et recherche avancés

**Hors Scope (V1) :**
- Streaming vidéo
- Application mobile native
- Intelligence Artificielle prédictive
- Intégration temps réel (live scores)

### 1.4 Méthodologie de Développement

**Approche Agile Itérative :**
- **Sprint 1 (Semaine 1-2)** : Conception BDD + ETL
- **Sprint 2 (Semaine 3-4)** : API Backend (FastAPI)
- **Sprint 3 (Semaine 5-6)** : Frontend & Design System
- **Sprint 4 (Semaine 7)** : Tests & Optimisation

**Outils de Gestion :**
- Git/GitHub pour le versioning
- Visual Studio Code comme IDE
- PostgreSQL pour la base de données
- Postman pour le test d'API

---

## 2. Architecture du Système

### 2.1 Vue d'Ensemble de l'Architecture

L'application suit une architecture **MVC (Modèle-Vue-Contrôleur)** adaptée au Web moderne, avec une séparation stricte des responsabilités.

**Schéma Architectural :**
```
┌─────────────────────────────────────────────────────────┐
│                    UTILISATEUR                          │
│                   (Navigateur Web)                      │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
                     ↓
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (Vue/Contrôleur)                  │
│   Jinja2 Templates + Tailwind CSS + JavaScript          │
│   - dashboard.html                                      │
│   - performance.html                                    │
│   - player_profile.html                                 │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP Requests (GET/POST)
                     ↓
┌─────────────────────────────────────────────────────────┐
│            BACKEND API (Contrôleur/Modèle)              │
│               FastAPI (Python 3.10+)                    │
│   - Routes & Endpoints                                  │
│   - Business Logic (GPI calculation)                    │
│   - Data Validation (Pydantic)                          │
└────────────────────┬────────────────────────────────────┘
                     │ SQL Queries (SQLAlchemy ORM)
                     ↓
┌─────────────────────────────────────────────────────────┐
│           BASE DE DONNÉES (Modèle)                      │
│              PostgreSQL 14+                             │
│   - Tables relationnelles                               │
│   - Indexation & Constraints                            │
└─────────────────────────────────────────────────────────┘
                     ↑
                     │ INSERT/UPDATE
┌─────────────────────────────────────────────────────────┐
│              PIPELINE ETL                                │
│          Python Scripts (Native)                        │
│   - extract/  - transform/  - load/                      │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Justification des Choix Techniques

#### 2.2.1 Backend : FastAPI

**Pourquoi FastAPI ?**
- **Performance** : Basé sur Starlette (ASGI), l'un des frameworks Python les plus rapides
- **Validation Automatique** : Pydantic assure la validation des données en entrée/sortie
- **Documentation Auto** : Génération automatique de Swagger UI
- **Asynchrone** : Support natif de async/await pour les opérations I/O
- **Type Hints** : Utilisation complète des annotations Python pour la sécurité de type

**Alternatives Considérées :**
- **Flask** : Plus simple mais moins performant, pas de validation intégrée
- **Django** : Trop lourd pour nos besoins, courbe d'apprentissage élevée
- **Node.js (Express)** : Bon choix mais équipe plus à l'aise avec Python

#### 2.2.2 Base de Données : PostgreSQL

**Pourquoi PostgreSQL ?**
- **Robustesse** : SGBDR mature et éprouvé
- **Types Avancés** : Support JSON, Arrays, enums
- **Performance** : Excellent optimizer, indexation B-Tree efficace
- **Intégrité** : Foreign keys, transactions ACID
- **Écosystème** : Excellente intégration avec SQLAlchemy

**Alternatives Considérées :**
- **MySQL** : Moins de features avancées, moins performant pour les requêtes complexes
- **SQLite** : Trop limité pour une application multi-utilisateurs
- **MongoDB** : NoSQL non adapté pour des données fortement relationnelles

#### 2.2.3 ORM : SQLAlchemy

**Avantages :**
- Abstraction du SQL brut
- Protection contre les injections SQL
- Migrations facilitées (Alembic)
- Lazy Loading & Eager Loading optimisés

#### 2.2.4 Frontend : Jinja2 + Tailwind CSS

**Jinja2 (Templating) :**
- Rendu côté serveur (SSR) pour de meilleures performances initiales
- SEO-friendly
- Pas de complexité SPA (React/Vue) pour un MVP

**Tailwind CSS :**
- Approche Utility-First : développement rapide
- Customisation complète via `tailwind.config.js`
- Optimisation automatique (PurgeCSS)
- Composants réutilisables via `@apply`

**JavaScript Vanilla :**
- Pas de dépendance à un framework lourd
- Meilleure performance
- Interaction simple (tri de tableaux, recherche)

#### 2.2.5 Visualisation : Plotly.js

**Pourquoi Plotly ?**
- Graphiques scientifiques de haute qualité
- Interactivité native (zoom, pan, hover)
- Support des Radar Charts et Scatter Plots
- Export PNG/SVG intégré

**Alternatives :**
- **Chart.js** : Plus simple mais moins de types de graphiques
- **D3.js** : Très puissant mais courbe d'apprentissage élevée

### 2.3 Structure du Projet

```
atlasperformance/
│
├── app/                      # Application Backend
│   ├── __init__.py
│   ├── main.py              # Point d'entrée FastAPI (Routes & Endpoints)
│   ├── database.py          # Configuration BDD (engine, session)
│   ├── models.py            # Modèles SQLAlchemy (Tables)
│   ├── exceptions.py        # Gestion des erreurs personnalisées
│   ├── init_db.py           # Initialisation de la base de données
│   ├── clean_db.py          # Scripts de nettoyage BDD
│   ├── check_results.py     # Vérification des résultats
│   ├── recalculate_ratings.py  # Recalcul des notes joueurs
│   ├── routers/             # Routes organisées par module
│   │   ├── competitions.py
│   │   ├── teams.py
│   │   ├── players.py
│   │   ├── matches.py
│   │   ├── performances.py
│   │   └── analytics.py
│   ├── schemas/             # Schémas Pydantic (Validation)
│   │   ├── competition.py
│   │   ├── team.py
│   │   ├── player.py
│   │   ├── match.py
│   │   └── performance.py
│   ├── services/            # Logique métier
│   │   ├── analytics.py
│   │   └── statistics.py
│   └── utils/               # Utilitaires
│       └── helpers.py
│
├── etl/                     # Pipeline ETL
│   ├── config.py            # Configuration ETL
│   ├── run_etl.py           # Script principal ETL
│   ├── fetch_match_stats.py # Récupération stats matchs
│   ├── extract/             # Extraction
│   │   ├── competitions.py
│   │   ├── teams.py
│   │   ├── players.py
│   │   └── matches.py
│   ├── transform/           # Transformation
│   │   ├── cleaners.py      # Nettoyage de données
│   │   └── validators.py    # Validation des données
│   ├── load/                # Chargement
│   │   └── loaders.py       # Insertion en BDD
│   └── utils/               # Utilitaires ETL
│       ├── http_client.py   # Client HTTP pour APIs
│       └── logger.py        # Logging
│
├── frontend/                # Interface Utilisateur
│   ├── static/
│   │   ├── css/             # Styles CSS
│   │   ├── js/              # Scripts JavaScript
│   │   └── images/          # Images & Assets
│   │       ├── logo.png
│   │       └── stadium_pitch.png
│   └── templates/
│       ├── layout/
│       │   └── base.html    # Template de base
│       ├── dashboard.html
│       ├── performance.html
│       ├── player_profile.html
│       ├── teams.html
│       ├── team_detail.html
│       ├── matches.html
│       ├── match_detail.html
│       ├── players.html
│       ├── competitions.html
│       └── about.html
│
├── data/                    # Données brutes (JSON)
│   ├── raw_json/           # Données joueurs/équipes
│   └── raw_json_StatistiqueMatches/  # Stats matchs
│
├── logs/                    # Logs d'exécution
│   ├── etl.log             # Logs ETL
│   └── etl_state.json      # État du pipeline ETL
│
├── scripts/                 # Scripts d'orchestration
│   ├── run_etl.ps1         # Orchestrateur ETL (PowerShell)
│   └── run_etl.sh          # Orchestrateur ETL (Bash)
│
├── tests/                   # Tests unitaires & d'intégration
│   ├── conftest.py         # Configuration Pytest
│   ├── test_api_competitions.py
│   ├── test_api_teams.py
│   ├── test_api_players.py
│   ├── test_api_matches.py
│   ├── test_api_performances.py
│   └── test_api_analytics.py
│
├── docs/                    # Documentation
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── ETL_GUIDE.md
│   ├── SETUP.md
│   ├── USER_GUIDE.md
│   └── presentation.md     # Document de présentation
│
├── Dockerfile              # Configuration Docker
├── docker-compose.yml      # Orchestration multi-conteneurs
├── .env                    # Variables d'environnement
├── .env.example            # Template variables d'env
├── .gitignore              # Fichiers ignorés par Git
├── requirements.txt        # Dépendances Python
├── run_migration.py        # Script de migration BDD
├── test_etl_setup.py       # Test setup ETL
└── README.md              # Documentation principale
```

---

## 3. Pipeline ETL & Ingénierie des Données

### 3.1 Stratégie d'Acquisition des Données (Extract)

#### 3.1.1 Sources de Données

**Source Principale :**
1. **API-Football (v3)** : Intégration directe via RapidAPI pour récupérer l'intégralité des données (Ligues, Équipes, Joueurs, Matchs, Statistiques).

**Stratégie de Cache :**
Pour optimiser les coûts et la performance, les réponses JSON sont stockées localement (`data/raw_json/`) et servent de cache persistants.

**Métadonnées Collectées :**
- **Compétitions** : Nom, Pays, Logo
- **Équipes** : Nom, Ville, Stade, Logo
- **Joueurs** : Nom, Date de naissance, Poste, Photo, Nationalité
- **Matchs** : Date, Score, Lieu, Arbitre
- **Performances** : Statistiques par joueur et par match (35+ métriques)

#### 3.1.2 Scripts d'Extraction

L'extraction est gérée par un client HTTP personnalisé (`etl.utils.http_client`) qui encapsule la logique de résilience (retries, rate limiting) et de mise en cache. Nous utilisons des flux de dictionnaires Python standards plutôt que pour cette phase, ce qui réduit la complexité et l'empreinte mémoire.

**Exemple : Extraction des matchs (`etl/extract/matches.py`)**

```python
from etl.utils.http_client import api_client
from etl.utils.logger import log_info, log_error
from datetime import datetime

def fetch_matches_by_league(league_id: int, season: int) -> list:
    """
    Récupère les matchs d'une ligue via l'endpoint /fixtures.
    Gère le rate limiting et le cache automatiquement.
    """
    log_info(f"Extraction matchs pour Ligue {league_id}...")
    
    # Appel API via notre wrapper client
    data = api_client.get("fixtures", params={"league": league_id, "season": season})
    
    if not data:
        return []

    cleaned_matches = []
    for item in data:
        try:
            fixture = item['fixture']
            # Parsing ISO Date avec gestion UTC
            match_date = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))

            cleaned_matches.append({
                "api_id": fixture['id'],
                "date": match_date,
                "status": fixture['status']['short'],
                "home_score": item['goals']['home'],
                "away_score": item['goals']['away'],
                "competition_api_id": league_id
            })
        except KeyError as e:
            log_error(f"Erreur parsing match {fixture['id']}: {e}")
            continue

    return cleaned_matches
```

### 3.2 Traitement & Nettoyage (Transform)

#### 3.2.1 Problèmes de Qualité de Données

**Issues Communes :**
1. **Valeurs Manquantes** : ~15% des champs "photo" sont vides
2. **Doublons** : Même joueur avec plusieurs orthographes
3. **Incohérences** : Formats de dates différents
4. **Outliers** : Valeurs aberrantes (ex: rating > 10)

#### 3.2.2 Stratégies de Nettoyage

#### 3.2.2 Stratégies de Nettoyage

**Gestion des Valeurs Manquantes & Typage (`etl/transform/cleaners.py`) :**
Nous utilisons des fonctions helpers pour sécuriser la conversion des types et gérer les `None`.

```python
def _safe_int(value: Any, default: int = 0) -> int:
    """Convertit en int de manière sûre, retourne une valeur par défaut si échec."""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def clean_performance_data(perf: dict) -> dict:
    return {
        # Imputation par défaut à 0 pour les stats numériques
        "minutes_played": _safe_int(perf.get('minutes_played'), 0),
        "goals": _safe_int(perf.get('goals'), 0),
        "assists": _safe_int(perf.get('assists'), 0),
        # Gestion des flottants
        "rating": _safe_float(perf.get('rating')), 
    }
```

**Normalisation des Noms :**
```python
def _clean_str(value: str) -> str:
    """Nettoyage standard des chaînes de caractères."""
    if isinstance(value, str):
        # Strip et formatage basique
        return value.strip()
    return None
```

**Calcul de Métriques : Note de Performance "Atlas" (`app/recalculate_ratings.py`) :**
Au lieu d'un index pondéré complexe type GPI, nous avons implémenté un algorithme de notation dynamique sur base 6.0, inspiré des systèmes de Fantasy Football.

```python
def calculate_custom_rating(perf):
    """
    Algorithme propriétaire Atlas pour la notation (1.0 - 10.0).
    """
    # 1. Base 6.0
    rating = 6.0
    
    # 2. Bonus
    rating += float(perf.goals or 0) * 1.0           # Buts
    rating += float(perf.assists or 0) * 0.8         # Passes D.
    rating += float(perf.shots_on_target or 0) * 0.2 # Tirs Cadrés
    rating += float(perf.saves or 0) * 0.5           # Arrêts (Gardiens)
    
    # Bonus Possession & Défense
    rating += float(perf.interceptions or 0) * 0.1
    rating += float(perf.dribbles_success or 0) * 0.1
    
    # 3. Malus
    rating -= float(perf.yellow_cards or 0) * 1.0
    rating -= float(perf.red_cards or 0) * 3.0
    rating -= float(perf.fouls_committed or 0) * 0.2
    
    # 4. Logique de Passes
    passes_total = perf.passes_total or 0
    if passes_total > 5:
        pass_rate = (perf.passes_accurate or 0) / passes_total
        if pass_rate > 0.85: rating += 0.3
        elif pass_rate < 0.70: rating -= 0.3

    # Clamping (Borner la note entre 1 et 10)
    return max(1.0, min(10.0, round(rating, 1)))
```

### 3.3 Chargement en Base (Load)

#### 3.3.1 Stratégie Upsert

**Problématique :** Comment gérer les mises à jour de joueurs existants ?

**Solution :** Implémentation d'un Upsert (Update or Insert)
```python
from sqlalchemy.dialects.postgresql import insert

def upsert_player(session, player_data):
    """
    Insère un joueur ou met à jour s'il existe.
    """
    stmt = insert(Player).values(**player_data)
    
    # En cas de conflit sur 'name', on update
    stmt = stmt.on_conflict_do_update(
        index_elements=['name'],
        set_=dict(
            position=stmt.excluded.position,
            photo=stmt.excluded.photo,
            updated_at=func.now()
        )
    )
    
    session.execute(stmt)
    session.commit()
```

#### 3.3.2 Gestion des Transactions

**Principe ACID :**
- **Atomicity** : Tout ou rien (rollback en cas d'erreur)
- **Consistency** : Respect des contraintes (foreign keys)
- **Isolation** : Transactions indépendantes
- **Durability** : Persistance garantie

```python
try:
    with engine.begin() as connection:
        # Insertion de multiples enregistrements
        for player in players_batch:
            insert_player(connection, player)
        # Commit automatique si pas d'erreur
except Exception as e:
    # Rollback automatique en cas d'erreur
    logger.error(f"Erreur ETL: {e}")
    raise
```

### 3.4 Automatisation du Pipeline

**Script Orchestrateur Unique :**
L'ensemble du pipeline ETL est automatisé via un seul script PowerShell qui orchestre toutes les étapes :

```powershell
# scripts/run_etl.ps1
Write-Host "[*] Lancement du Pipeline ETL AtlasPerformance..." -ForegroundColor Green

# 1. Vérification que le conteneur Docker est actif
if (-not (docker ps -q -f name=atlas_app)) {
    Write-Host "[!] [ERREUR] Le conteneur 'atlas_app' ne tourne pas." -ForegroundColor Red
    Write-Host "Veuillez lancer 'docker-compose up -d' d'abord."
    exit 1
}

# 2. Exécution du Pipeline ETL complet (Extract, Transform, Load)
Write-Host "[*] Exécution du pipeline ETL..." -ForegroundColor Cyan
docker-compose exec web python -m etl.run_etl --mode full

# 3. Récupération des statistiques avancées de matchs
Write-Host "[*] Récupération des statistiques de matchs..." -ForegroundColor Cyan
docker-compose exec -T web python -m etl.fetch_match_stats

# 4. Recalcul des notes joueurs (algorithme personnalisé)
Write-Host "[*] Recalcul des notes joueurs..." -ForegroundColor Cyan
docker-compose exec -T web python -m app.recalculate_ratings

Write-Host "[OK] Pipeline ETL terminé avec succès!" -ForegroundColor Green
```

**Commande d'Exécution :**
```powershell
# Lancer l'ensemble du pipeline ETL en une seule commande
.\scripts\run_etl.ps1
```

**Étapes Automatisées :**
1. **Vérification Environnement** : S'assure que Docker est actif
2. **ETL Core** : Extraction, transformation et chargement des données
3. **Statistiques Avancées** : Récupération des métriques de matchs
4. **Post-Processing** : Recalcul des indices de performance

---

## 4. Conception de la Base de Données

### 4.1 Modèle Conceptuel (MCD)

**Entités Principales :**
1. **Competition** : Représente une compétition (Ligue, Coupe)
2. **Team** : Équipe de football
3. **Player** : Joueur individuel
4. **Match** : Rencontre entre deux équipes
5. **Performance** : Statistiques d'un joueur lors d'un match

**Relations :**
- Une **Competition** contient plusieurs **Team** (1:N)
- Une **Team** possède plusieurs **Player** (1:N)
- Un **Match** implique deux **Team** (home/away) (N:1 x2)
- Un **Match** génère plusieurs **Performance** (1:N)
- Un **Player** réalise plusieurs **Performance** (1:N)

### 4.2 Modèle Logique de Données (MLD)

**Diagramme ERD :**
```
┌─────────────────┐
│  COMPETITION    │
│─────────────────│
│ id (PK)         │
│ name            │
│ country         │
│ logo            │
└────────┬────────┘
         │ 1:N
         ↓
┌─────────────────┐        ┌─────────────────────────────┐
│     TEAM        │   N:1  │         MATCH               │
│─────────────────│◄───────│─────────────────────────────│
│ id (PK)         │        │ id (PK)                     │
│ name            │        │ date                        │
│ logo            │        │ home_team_id(FK)            │
│ competition_id  │        │ away_team_id(FK)            │
└────────┬────────┘        │ home_score, away_score      │
         │ 1:N             └──────┬───────────────┬──────┘
         ↓                        │ 1:N           │ 1:N
┌─────────────────┐               ↓               ↓
│     PLAYER      │      ┌─────────────── ─┐  ┌──────────────────────┐
│─────────────────│      │  PERFORMANCE    │  │  MATCH_STATISTICS    │
│ id (PK)         │  N:1 │──────────────── │  │──────────────────────│
│ name            │◄─────│ id (PK)         │  │ id (PK)              │
│ position        │      │ match_id (FK)   │  │ match_id (FK)        │
│ photo           │      │ player_id (FK)  │  │ team_id (FK)         │
│ team_id (FK)    │      │ rating          │  │ shots_total          │
│ nationality     │      │ goals, assists  │  │ ball_possession      │
└─────────────────┘      │ passes_total    │  │ corners, offsides    │
                         │ yellow/red_cards│  │ goalkeeper_saves     │
                         └─────────────────┘  └──────────────────────┘
```

### 4.3 Dictionnaire de Données Détaillé

#### Table : `competitions`
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identifiant unique |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Nom de la compétition |
| country | VARCHAR(50) | NOT NULL | Pays organisateur |
| logo | TEXT | NULL | URL du logo |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |

#### Table : `teams`
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identifiant unique |
| name | VARCHAR(100) | NOT NULL | Nom de l'équipe |
| logo | TEXT | NULL | URL du logo |
| competition_id | INTEGER | FOREIGN KEY | Référence à competition.id |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |

#### Table : `players`
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identifiant unique |
| name | VARCHAR(100) | NOT NULL | Nom complet du joueur |
| position | VARCHAR(20) | NULL | Poste (GK, DF, MF, FW) |
| photo | TEXT | NULL | URL photo profil |
| nationality | VARCHAR(50) | NULL | Nationalité |
| date_of_birth | DATE | NULL | Date de naissance |
| team_id | INTEGER | FOREIGN KEY | Référence à team.id |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |

#### Table : `matches`
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identifiant unique |
| date | DATE | NOT NULL | Date du match |
| home_team_id | INTEGER | FOREIGN KEY | Équipe domicile |
| away_team_id | INTEGER | FOREIGN KEY | Équipe extérieur |
| home_score | INTEGER | NULL | Score domicile |
| away_score | INTEGER | NULL | Score extérieur |
| competition_id | INTEGER | FOREIGN KEY | Compétition |
| created_at | TIMESTAMP | DEFAULT NOW() | Date création |

#### Table : `performances`
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identifiant unique |
| match_id | INTEGER | FOREIGN KEY, NOT NULL | Référence match |
| player_id | INTEGER | FOREIGN KEY, NOT NULL | Référence joueur |
| player_name | VARCHAR(100) | NULL | Nom du joueur (dénormalisé) |
| team_api_id | INTEGER | NULL | ID API de l'équipe |
| rating | DECIMAL(3,2) | NULL | Note SofaScore (0-10) |
| minutes_played | INTEGER | DEFAULT 0 | Minutes jouées |
| goals | INTEGER | DEFAULT 0 | Buts marqués |
| assists | INTEGER | DEFAULT 0 | Passes décisives |
| shots_total | INTEGER | DEFAULT 0 | Tirs totaux |
| shots_on_target | INTEGER | DEFAULT 0 | Tirs cadrés |
| passes_total | INTEGER | DEFAULT 0 | Passes tentées |
| passes_accurate | INTEGER | DEFAULT 0 | Passes réussies |
| tackles | INTEGER | DEFAULT 0 | Tacles |
| interceptions | INTEGER | DEFAULT 0 | Interceptions |
| fouls_committed | INTEGER | DEFAULT 0 | Fautes commises |
| fouls_drawn | INTEGER | DEFAULT 0 | Fautes subies |
| yellow_cards | INTEGER | DEFAULT 0 | Cartons jaunes |
| red_cards | INTEGER | DEFAULT 0 | Cartons rouges |
| saves | INTEGER | DEFAULT 0 | Arrêts (gardiens) |
| dribbles_success | INTEGER | DEFAULT 0 | Dribbles réussis |
| created_at | TIMESTAMP | DEFAULT NOW() | Date création |

#### Table : `match_statistics`
| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Identifiant unique |
| match_id | INTEGER | FOREIGN KEY | Référence match |
| team_id | INTEGER | FOREIGN KEY | Référence équipe |
| shots_total | INTEGER | DEFAULT 0 | Tirs totaux |
| shots_on_goal | INTEGER | DEFAULT 0 | Tirs cadrés |
| shots_off_goal | INTEGER | DEFAULT 0 | Tirs non cadrés |
| shots_blocked | INTEGER | DEFAULT 0 | Tirs bloqués |
| shots_inside_box | INTEGER | DEFAULT 0 | Tirs dans la surface |
| shots_outside_box | INTEGER | DEFAULT 0 | Tirs hors surface |
| fouls | INTEGER | DEFAULT 0 | Fautes commises |
| corners | INTEGER | DEFAULT 0 | Corners |
| offsides | INTEGER | DEFAULT 0 | Hors-jeux |
| ball_possession | VARCHAR(10) | DEFAULT "50%" | Possession (%) |
| yellow_cards | INTEGER | DEFAULT 0 | Cartons jaunes |
| red_cards | INTEGER | DEFAULT 0 | Cartons rouges |
| goalkeeper_saves | INTEGER | DEFAULT 0 | Arrêts du gardien |
| passes_total | INTEGER | DEFAULT 0 | Passes totales |
| passes_accurate | INTEGER | DEFAULT 0 | Passes réussies |
| created_at | TIMESTAMP | DEFAULT NOW() | Date création |
| updated_at | TIMESTAMP | ON UPDATE NOW() | Date modification |

**Contraintes Additionnelles :**
```sql
-- Unicité : un joueur ne peut avoir qu'une performance par match
ALTER TABLE performances 
ADD CONSTRAINT unique_player_match 
UNIQUE (player_id, match_id);

-- Check : le score ne peut être négatif
ALTER TABLE matches 
ADD CONSTRAINT positive_score 
CHECK (home_score >= 0 AND away_score >= 0);

-- Check : les minutes jouées entre 0 et 120
ALTER TABLE performances 
ADD CONSTRAINT valid_minutes 
CHECK (minutes >= 0 AND minutes <= 120);
```

### 4.4 Indexation pour Performance

**Index B-Tree (Performance Queries) :**
```sql
-- Index sur les clés étrangères pour les JOINs
CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_performances_match ON performances(match_id);
CREATE INDEX idx_performances_player ON performances(player_id);
CREATE INDEX idx_matches_home_team ON matches(home_team_id);
CREATE INDEX idx_matches_away_team ON matches(away_team_id);

-- Index sur les colonnes de filtrage fréquent
CREATE INDEX idx_players_position ON players(position);
CREATE INDEX idx_matches_date ON matches(date DESC);

-- Index composite pour les requêtes complexes
CREATE INDEX idx_perf_player_minutes ON performances(player_id, minutes);
```

**Résultats Benchmarks :**
- Requête sans index : ~450ms (10k records)
- Requête avec index : ~8ms (10k records)
- **Amélioration : 56x**

---

## 5. Développement Backend

### 5.1 Architecture FastAPI

#### 5.1.1 Point d'Entrée (main.py)

```python
# app/main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, crud
from .database import engine, get_db

# Création des tables si elles n'existent pas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Atlas Performance API",
    description="API pour l'analytics footballistique",
    version="1.0.0"
)

# Configuration des fichiers statiques et templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    """Page d'accueil - Redirection vers dashboard"""
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
def dashboard(
    request: Request,
    competition_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Dashboard principal avec KPIs et widgets
    """
    # Récupération des statistiques globales
    stats = crud.get_global_stats(db, competition_id)
    
    # Top 10 buteurs
    top_scorers = crud.get_top_scorers(db, limit=10, competition_id=competition_id)
    
    # Matchs récents
    recent_matches = crud.get_recent_matches(db, limit=4, competition_id=competition_id)
    
    # Équipe de la semaine (meilleurs joueurs)
    team_of_week = crud.get_team_of_week(db, competition_id=competition_id)
    
    # Liste des compétitions pour le filtre
    competitions = crud.get_all_competitions(db)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "top_scorers": top_scorers,
            "recent_matches": recent_matches,
            "team_of_week": team_of_week,
            "competitions_list": competitions,
            "selected_competition_id": competition_id
        }
    )
```

#### 5.1.2 Services & Logique Métier

La logique métier est organisée dans `app/services/` et directement dans les fonctions de routes de `app/main.py`.

**Exemple : Calcul des statistiques globales (app/main.py)**
```python
# app/main.py
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app import models

def get_global_stats(db: Session, competition_id: int = None):
    """
    Calcule les KPIs globaux pour le dashboard
    
    Returns:
        dict: {
            'matches_played': int,
            'goals_scored': int,
            'yellow_cards': int,
            'red_cards': int
        }
    """
    # Construction de la query de base
    query = db.query(
        func.count(distinct(models.Match.id)).label('matches_played'),
        func.sum(models.Performance.goals).label('goals_scored'),
        func.sum(models.Performance.yellow_cards).label('yellow_cards'),
        func.sum(models.Performance.red_cards).label('red_cards')
    ).join(models.Match)
    
    # Filtre optionnel par compétition
    if competition_id:
        query = query.filter(models.Match.competition_id == competition_id)
    
    result = query.first()
    
    return {
        'matches_played': result.matches_played or 0,
        'goals_scored': int(result.goals_scored or 0),
        'yellow_cards': int(result.yellow_cards or 0),
        'red_cards': int(result.red_cards or 0)
    }
```

**Exemple : Top Scorers avec agrégation (app/main.py)**
```python
def get_top_scorers(db: Session, limit: int = 10, competition_id: int = None):
    """
    Récupère le classement des meilleurs buteurs
    """
    query = db.query(
        models.Player.id,
        models.Player.name,
        models.Player.photo,
        models.Team.name.label('team_name'),
        func.count(distinct(models.Performance.match_id)).label('matches_played'),
        func.sum(models.Performance.goals).label('total_goals'),
        func.avg(models.Performance.rating).label('avg_rating')
    ).join(models.Performance) \
     .join(models.Team) \
     .join(models.Match, models.Performance.match_id == models.Match.id)
    
    # Filtrage par compétition si spécifié
    if competition_id:
        query = query.filter(models.Match.competition_id == competition_id)
    
    # Groupement et tri
    query = query.group_by(
        models.Player.id,
        models.Player.name,
        models.Player.photo,
        models.Team.name
    ).having(func.sum(models.Performance.goals) > 0) \
     .order_by(func.sum(models.Performance.goals).desc()) \
     .limit(limit)
    
    return query.all()
```

### 5.2 Endpoint de Performance (Recherche Avancée)

```python
@app.get("/performance")
def performance_page(
    request: Request,
    competition_id: str = None,
    team_id: str = None,
    position: str = None,
    min_minutes: int = 90,
    db: Session = Depends(get_db)
):
    """
    Page de recherche avancée avec filtres dynamiques
    """
    # Conversion des paramètres string en int (gestion des "")
    comp_id = int(competition_id) if competition_id and competition_id != "" else None
    t_id = int(team_id) if team_id and team_id != "" else None
    
    # Construction de la requête de base
    query = db.query(
        models.Player.id,
        models.Player.name,
        models.Player.position,
        models.Player.photo,
        models.Team.name.label('team_name'),
        func.count(distinct(models.Performance.match_id)).label('matches_played'),
        func.sum(models.Performance.minutes).label('total_minutes'),
        func.sum(models.Performance.goals).label('total_goals'),
        func.sum(models.Performance.assists).label('total_assists'),
        func.avg(models.Performance.rating).label('avg_rating')
    ).select_from(models.Performance) \
     .join(models.Match, models.Performance.match_id == models.Match.id) \
     .join(models.Player) \
     .join(models.Team)
    
    # Application des filtres
    if comp_id:
        query = query.filter(models.Match.competition_id == comp_id)
    if t_id:
        query = query.filter(models.Player.team_id == t_id)
    if position:
        query = query.filter(models.Player.position == position)
    
    # Groupement
    query = query.group_by(
        models.Player.id,
        models.Player.name,
        models.Player.position,
        models.Player.photo,
        models.Team.name
    )
    
    # Filtre sur minutes totales
    if min_minutes:
        query = query.having(func.sum(models.Performance.minutes) >= min_minutes)
    
    # Exécution et transformation
    players_data = query.all()
    
    # Calcul des métriques dérivées (Per 90, GPI)
    players_list = []
    for p in players_data:
        total_90s = p.total_minutes / 90 if p.total_minutes > 0 else 1
        
        # Calcul de la précision de passe (nécessite d'étendre la query)
        pass_accuracy = calculate_pass_accuracy(db, p.id)
        
        # Calcul du GPI
        gpi = calculate_player_gpi(
            avg_rating=p.avg_rating or 0,
            goals_per_90=p.total_goals / total_90s,
            assists_per_90=p.total_assists / total_90s,
            pass_accuracy=pass_accuracy
        )
        
        players_list.append({
            'id': p.id,
            'name': p.name,
            'position': p.position,
            'photo': p.photo,
            'team_name': p.team_name,
            'matches_played': p.matches_played,
            'total_minutes': p.total_minutes,
            'total_goals': p.total_goals,
            'total_assists': p.total_assists,
            'avg_rating': round(p.avg_rating, 2) if p.avg_rating else 0,
            'goals_per_90': round(p.total_goals / total_90s, 2),
            'assists_per_90': round(p.total_assists / total_90s, 2),
            'pass_accuracy': pass_accuracy,
            'gpi': gpi
        })
    
    # Récupération des données pour les filtres
    competitions = crud.get_all_competitions(db)
    teams = crud.get_all_teams(db)
    
    return templates.TemplateResponse(
        "performance.html",
        {
            "request": request,
            "players": players_list,
            "competitions_list": competitions,
            "teams_list": teams,
            "selected_competition_id": comp_id,
            "selected_team_id": t_id,
            "selected_position": position,
            "selected_min_minutes": min_minutes
        }
    )
```

### 5.3 Validation avec Pydantic (Schemas)

```python
# app/schemas.py
from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import date

class PlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    position: Optional[str] = Field(None, regex="^(GK|DF|MF|FW)$")
    photo: Optional[str] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or v.isspace():
            raise ValueError('Name cannot be empty')
        return v.strip()

class PlayerCreate(PlayerBase):
    team_id: int

class PlayerResponse(PlayerBase):
    id: int
    team_name: str
    
    class Config:
        orm_mode = True  # Permet la conversion depuis un modèle SQLAlchemy
```

### 5.4 Gestion des Erreurs

```python
from fastapi import HTTPException, status

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal Server Error: {exc}")
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=500
    )
```

---

## 6. Interface Utilisateur (UI/UX)

### 6.1 Design System "Dark Premium"

#### 6.1.1 Philosophie de Design

**Inspirations :**
- **ESPN Analytics** : Tableaux de bord sportifs professionnels
- **SofaScore** : Interface dark et statistiques détaillées
- **DataViz** : Visualisations claires et actionnables

**Principes Directeurs :**
1. **Dark First** : Réduction de la fatigue oculaire pour de longues sessions
2. **Hiérarchie Claire** : Information importante = Couleurs vives (Cyan/Gold)
3. **Interactions Fluides** : Animations subtiles (transitions 300ms)
4. **Responsive** : Mobile-first approach

#### 6.1.2 Palette de Couleurs

```css
/* Couleurs Principales */
:root {
  /* Backgrounds */
  --bg-primary: #0f172a;      /* slate-900 */
  --bg-secondary: #1e293b;    /* slate-800 */
  --bg-tertiary: #334155;     /* slate-700 */
  
  /* Accents */
  --accent-cyan: #06b6d4;     /* Atlas Cyan */
  --accent-gold: #eab308;     /* Atlas Gold */
  --accent-green: #10b981;    /* Succès/Performance */
  
  /* Textes */
  --text-primary: #ffffff;
  --text-secondary: #cbd5e1;  /* slate-300 */
  --text-muted: #94a3b8;      /* slate-400 */
  
  /* Statuts */
  --status-success: #10b981;
  --status-warning: #f59e0b;
  --status-danger: #ef4444;
}
```

#### 6.1.3 Typographie

```css
/* Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--bg-primary);
}

/* Hiérarchie Titres */
h1 { font-size: 2.5rem; font-weight: 800; }
h2 { font-size: 2rem; font-weight: 700; }
h3 { font-size: 1.5rem; font-weight: 600; }
h4 { font-size: 1.25rem; font-weight: 600; }
```

### 6.2 Composants UI Personnalisés

#### 6.2.1 Cards "Glassmorphism"

```css
.card-premium {
  background: rgba(30, 41, 59, 0.8);  /* slate-800 avec transparence */
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.card-premium:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(6, 182, 212, 0.15);
  border-color: rgba(6, 182, 212, 0.3);
}
```

#### 6.2.2 Logos Hexagonaux (Équipes)

**Challenge Technique :** CSS ne supporte pas nativement les hexagones.

**Solution :** Utilisation de `clip-path` avec polygones

```css
/* Hexagone Flat-Topped (points gauche/droite) */
.logo-hexagon {
  width: 90px;
  height: 55px;
  clip-path: polygon(
    25% 0%,    /* Top-Left */
    75% 0%,    /* Top-Right */
    100% 50%,  /* Right */
    75% 100%,  /* Bottom-Right */
    25% 100%,  /* Bottom-Left */
    0% 50%     /* Left */
  );
  object-fit: cover;
  transition: transform 0.5s ease;
}

.logo-hexagon:hover {
  transform: scale(1.1) rotate(3deg);
}
```

**Implémentation HTML (Double Layer pour bordure blanche) :**
```html
<div class="relative w-[90px] h-[55px]">
  <!-- Conteneur blanc (bordure) -->
  <div class="absolute inset-0 bg-white clip-path-hex flex items-center justify-center">
    <!-- Image intérieure (légèrement plus petite) -->
    <img src="team_logo.png" 
         class="w-[86px] h-[51px] clip-path-hex object-cover">
  </div>
</div>
```

#### 6.2.3 Bento Grid Layout

**Principe :** Organisation en grille asymétrique inspirée des bento japonais

```html
<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
  <!-- KPI Cards (Full Width Mobile, 4 Cols Desktop) -->
  <div class="card-premium">Matchs Joués</div>
  <div class="card-premium">Buts Marqués</div>
  <div class="card-premium">Cartons Jaunes</div>
  <div class="card-premium">Cartons Rouges</div>
  
  <!-- Recent Matches (Spans 4 Cols) -->
  <div class="lg:col-span-4 card-premium">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <!-- 4 Match Cards -->
    </div>
  </div>
  
  <!-- Top Scorers (Spans 2 Cols) -->
  <div class="lg:col-span-2 card-premium">
    <!-- Table -->
  </div>
  
  <!-- Team of Week (Spans 2 Cols) -->
  <div class="lg:col-span-2 card-premium">
    <!-- 4-3-3 Formation -->
  </div>
</div>
```

### 6.3 Visualisations de Données

#### 6.3.1 Scatter Plot (Plotly.js)

**Objectif :** Corréler Productivité (Goals+Assists) vs Minutes Jouées

```javascript
// Configuration du graphique
const scatterData = [{
  x: playersData.map(p => p.total_minutes),
  y: playersData.map(p => p.total_goals + p.total_assists),
  mode: 'markers',
  marker: {
    size: playersData.map(p => p.total_goals * 3),  // Taille = buts
    color: playersData.map(p => p.avg_rating),      // Couleur = note
    colorscale: 'Viridis',
    showscale: true,
    colorbar: {
      title: 'Avg Rating',
      titleside: 'right'
    }
  },
  text: playersData.map(p => p.name),
  hovertemplate: '<b>%{text}</b><br>Minutes: %{x}<br>G+A: %{y}<extra></extra>'
}];

const layout = {
  title: 'Productivité vs Temps de Jeu',
  xaxis: { title: 'Minutes Jouées' },
  yaxis: { title: 'Buts + Passes Décisives' },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(30, 41, 59, 0.5)',
  font: { color: '#fff' }
};

Plotly.newPlot('scatter-chart', scatterData, layout, {responsive: true});
```

#### 6.3.2 Radar Chart (Profil Joueur)

```javascript
const radarData = [{
  type: 'scatterpolar',
  r: [playerStats.attacking, playerStats.defending, playerStats.technical, 
      playerStats.physical, playerStats.mental],
  theta: ['Attaque', 'Défense', 'Technique', 'Physique', 'Mental'],
  fill: 'toself',
  fillcolor: 'rgba(6, 182, 212, 0.3)',
  line: { color: '#06b6d4' }
}];

const radarLayout = {
  polar: {
    radialaxis: {
      visible: true,
      range: [0, 10],
      gridcolor: 'rgba(255,255,255,0.2)'
    },
    angularaxis: {
      gridcolor: 'rgba(255,255,255,0.2)'
    }
  },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: '#fff' }
};
```

### 6.4 Interactions JavaScript

#### 6.4.1 Tri de Tableau (Multi-Colonnes)

**Fonctionnalité :** Tri Excel-style avec support de 3 niveaux

```javascript
let sortStack = [];  // Stack pour mémoriser l'ordre des tris
let originalRows = []; // Ordre initial

function sortTable(columnIndex) {
  const table = document.getElementById('performanceTable');
  const tbody = table.querySelector('tbody');
  let rows = Array.from(tbody.rows);
  
  // Sauvegarder l'ordre original au premier tri
  if (originalRows.length === 0) {
    originalRows = rows.slice();
  }
  
  // Gestion du stack de tri
  const existingIndex = sortStack.findIndex(s => s.column === columnIndex);
  
  if (existingIndex !== -1) {
    // Cycle: Asc -> Desc -> Default
    const currentDir = sortStack[existingIndex].direction;
    if (currentDir === 'asc') {
      sortStack[existingIndex].direction = 'desc';
    } else {
      sortStack.splice(existingIndex, 1);  // Retour au défaut
    }
  } else {
    // Nouveau tri: ajouter en Primary
    sortStack.unshift({ column: columnIndex, direction: 'asc' });
  }
  
  // Limiter à 3 niveaux
  if (sortStack.length > 3) sortStack.length = 3;
  
  // Tri effectif
  if (sortStack.length === 0) {
    // Restaurer l'ordre original
    rows = originalRows.slice();
  } else {
    rows.sort((a, b) => {
      for (let i = 0; i < sortStack.length; i++) {
        const { column, direction } = sortStack[i];
        const cellA = a.cells[column].innerText.trim();
        const cellB = b.cells[column].innerText.trim();
        
        // Détection numérique
        const numA = parseFloat(cellA);
        const numB = parseFloat(cellB);
        const isNumeric = !isNaN(numA) && !isNaN(numB);
        
        let comparison = 0;
        if (isNumeric) {
          comparison = numA - numB;
        } else {
          comparison = cellA.localeCompare(cellB);
        }
        
        if (comparison !== 0) {
          return direction === 'asc' ? comparison : -comparison;
        }
      }
      return 0;
    });
  }
  
  // Réafficher les lignes triées
  const fragment = document.createDocumentFragment();
  rows.forEach(row => fragment.appendChild(row));
  tbody.appendChild(fragment);
  
  updateSortIcons();
}
```

#### 6.4.2 Recherche Instantanée

```javascript
function searchTable() {
  const input = document.getElementById('searchInput');
  const filter = input.value.toLowerCase();
  const table = document.getElementById('performanceTable');
  const rows = table.querySelectorAll('tbody tr');
  
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(filter) ? '' : 'none';
  });
  
  // Mise à jour du compteur de résultats
  const visibleCount = Array.from(rows).filter(r => r.style.display !== 'none').length;
  document.getElementById('resultCount').textContent = `${visibleCount} résultat(s)`;
}
```

#### 6.4.3 Export CSV

```javascript
function exportTableToCSV() {
  const table = document.getElementById('performanceTable');
  let csv = [];
  
  // Headers
  const headers = Array.from(table.querySelectorAll('thead th'))
    .map(th => th.textContent.trim());
  csv.push(headers.join(','));
  
  // Rows (seulement les lignes visibles)
  const rows = Array.from(table.querySelectorAll('tbody tr'))
    .filter(row => row.style.display !== 'none');
  
  rows.forEach(row => {
    const cells = Array.from(row.cells)
      .map(cell => `"${cell.textContent.trim()}"`);
    csv.push(cells.join(','));
  });
  
  // Téléchargement
  const csvContent = csv.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.href = url;
  link.download = `atlas_performance_${new Date().toISOString().split('T')[0]}.csv`;
  link.click();
  
  URL.revokeObjectURL(url);
}
```

---

---

## 7. Fonctionnalités Détaillées

### 7.1 Dashboard Global

**Page d'accueil** : Vue d'ensemble complète de toutes les statistiques.

**Composants Principaux :**
1. **Filtre Compétition** : Boutons chips interactifs pour filtrer par compétition ou afficher les stats globales
2. **KPI Cards Cliquables** :
   - **Matchs Joués** : Affiche le nombre total de matchs, cliquable vers `/matches`
   - **Buts Marqués** : Total des buts avec icône dégradée
   - **Cartons Jaunes** : Statistiques disciplinaires
   - **Cartons Rouges** : Expulsions
3. **Matchs Récents** : Grille responsive de 4 matchs avec logos hexagonaux, scores et status
4. **Top 10 Buteurs** : Classement avec photos, équipes, buts et notes moyennes
5. **Équipe de la Semaine (Team of the Week)** :
   - Formation tactique 4-3-3 sur fond de terrain
   - Photos des joueurs positionnées selon leur rôle
   - Notes individuelles affichées

**Innovations Design :**
- Logos hexagonaux "flat-topped" (format paysage)
- Effets glassmorphism et glow
- Bento Grid asymétrique

### 7.2 Performance Analytics

**Outil avancé d'analyse** de performances joueurs.

**Barre de Filtres Sticky :**
- **Compétition** : Sélection par dropdown avec auto-submit
- **Équipe** : Filtre dynamique
- **Position** : GK / DF / MF / FW
- **Minutes Minimales** : Input numérique

**Tableau Interactif Principal :**
- **Tri Multi-Colonnes** : Jusqu'à 3 niveaux simultanés (Excel-style)
- **Recherche Instantanée** : Filtrage en temps réel avec compteur de résultats
- **Colonnes** : Photo, Nom, Équipe, Position, Matchs, Minutes, Buts, Assists, Note moyenne, Per 90, GPI
- **Lignes Cliquables** : Redirection vers profil joueur
- **Export CSV** : Bouton pour télécharger les données filtrées

**Visualisations Plotly :**
- **Scatter Plot** : Productivité (G+A) vs Minutes jouées
  - Taille des points = Nombre de buts
  - Couleur = Note moyenne
- **Bar Chart** : Discipline par équipe (cartons jaunes/rouges)
- **Reset Zoom Custom** : Boutons personnalisés sur chaque graphique

### 7.3 Teams Directory (Annuaire des Équipes)

**Page dédiée** aux équipes avec recherche et filtres.

**Fonctionnalités :**
- **Recherche Dynamique** : Input avec debouncing (300ms) qui met à jour la grille en temps réel
- **Filtre Compétition** : Chips pour filtrer par ligue
- **Grille Responsive** : Layout adaptatif (1 col mobile → 4 cols desktop)

**Carte Équipe :**
- Logo hexagonal animé (hover: scale + rotation)
- Nom de l'équipe
- Badge de note moyenne (code couleur : vert si ≥ 7, ambre sinon)
- Pays
- Mini-stats : Matchs joués, Buts marqués, Note moyenne
- Cliquable vers page détaillée de l'équipe

### 7.4 Matches Calendar (Calendrier des Match project)

**Liste complète** des matchs avec filtres.

**Éléments Affichés :**
- **Filtre Compétition** : Chips pour navigation rapide
- **Compteur** : Affiche le nombre total de matchs trouvés

**Carte Match :**
- **Date &  Heure** : Formatage lisible
- **Compétition** : Badge coloré
- **Équipes** : Logos hexagonaux + noms
- **Score** : Affichage central avec status (FT / Upcoming)
- **Responsive** : Noms raccourcis sur mobile

### 7.5 Players Database

**Base de données joueurs** avec filtrage multi-critères.

**Filtres Avancés :**
- **Recherche** : Par nom, debounced
- **Compétition** : Chips globaux
- **Équipe** : Dropdown avec toutes les équipes
- **Position** : GK / DF / MF / FW

**Table Responsive :**
- **Colonnes** : Photo (avec fallback UI Avatars), Nom, Nationalité, Équipe (avec logo), Poste, Matchs, Buts, Note
- **Lignes Cliquables** : Navigation vers profil
- **Photo Joueur** : Affichage dans avatar circulaire
- **Badge Note** : Code couleur selon performance
- **Pagination** : Header avec compteur

### 7.6 Team Detail (Page Équipe)

**Fiche détaillée** d'une équipe spécifique.

**Sections :**
- **Header** : Logo, Nom, Pays, Stats globales (Matchs, Buts, Note)
- **Squad (Effectif)** : Liste des joueurs de l'équipe avec photos et stats
- **Recent Matches** : Historique des derniers matchs
- **Team Statistics** : Graphiques de performance collective

### 7.7 Match Detail (Détails du Match)

**Analyse complète** d'un match spécifique.

**Informations Affichées :**
- **Header** : Date, Compétition, Stade, Score final
- **Team Lineups** : Compositions d'équipes
- **Match Statistics** : Graphiques comparatifs (possession, tirs, passes)
  - Shots (total, on goal, off goal, blocked)
  - Ball Possession (%)
  - Corners & Offsides
  - Goalkeeper Saves
- **Player Performances** : Liste des performances individuelles avec notes
- **Timeline** : Événements clés du match (buts, cartons)

### 7.8 Player Profile (Profil Joueur)

**Fiche individuelle** détaillée.

**Header Héroïque :**
- Photo grand format
- Nom, Nationalité, Position
- Badge de note globale (circulaire)
- Équipe actuelle

**Statistiques Totales :**
- Matchs joués, Minutes
- Buts, Assists, Tirs
- Passes (total/accurate), Précision %
- Tacles, Interceptions
- Discipline (cartons)

**Métriques Avancées :**
- **Per 90** : Goals/90, Assists/90
- **GPI** : Global Performance Index

**Visualisations :**
- **Radar Chart** : Profil polyvalent (5+ axes)
- **Bar Chart** : Historique des 5 derniers matchs
- **Heatmap** : (Prévu) Zones d'activité

### 7.9 Competitions Hub

**Page centrale** des compétitions.

**Fonctionnalités :**
- Liste de toutes les compétitions disponibles
- Logos et drapeaux des pays
- Nombre d'équipes et de matchs par compétition
- Navigation vers les matchs de chaque compétition

### 7.10 About (À Propos)

**Page institutionnelle** du projet.

**Contenu :**
- Présentation du projet Atlas Performance
- Mission et objectifs
- Technologies utilisées
- Informations sur l'équipe de développement

---

## 8. Technologies & Outils

### 8.1 Stack Complet

| Catégorie | Technologie | Rôle |
|-----------|-------------|------|
| **Backend** | Python 3.10+ | Langage principal |
| | FastAPI | Framework Web |
| | SQLAlchemy | ORM |
| | Pydantic | Validation |
| | Uvicorn | Serveur ASGI |
| **Database** | PostgreSQL 14 (Docker) | SGBDR |
| | pgAdmin (Docker) | Gestion BDD |
| **Frontend** | Jinja2 | Templating |
| | Tailwind CSS (CDN) | Styling |
| | JavaScript ES6 | Interactivité |
| | Plotly.js | Visualisation |
| **ETL** | Python Custom Scripts | Extraction & Load |
| | Requests | API Consumption |
| **DevOps** | Docker & Compose | Containerization |
| | Git/GitHub | Version Control |
| | PowerShell | Scripting |
| **IDE** | VS Code | Développement |
| **Testing** | Pytest | Unit Testing |

### 8.2 Dépendances Python (requirements.txt)

```txt
# Framework Web & Serveur
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Base de données & ORM
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Data Engineering & Communication
requests==2.31.0

# Utilitaires & Configuration
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Tests & Template
pytest==7.4.3
jinja2==3.1.2
httpx==0.25.1
```

### 8.3 Configuration Tailwind (Via CDN dans base.html)

```javascript
// Configuration injectée directement dans le <head> du layout
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                slate: {
                    850: '#16181d', // Card Background
                    900: '#0e1015', // Main Background
                },
                atlas: {
                    cyan: '#06b6d4',  // Primary Brand
                    green: '#10B981', // Success
                    gold: '#F59E0B',  // Warning
                    red: '#F43F5E',   // Danger
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            }
        }
    }
}
```

---

## 9. Bilan & Perspectives

### 9.1 Réalisations

**Fonctionnalités Implémentées :**
✅ Pipeline ETL complet et automatisé
✅ Base de données optimisée
✅ API Backend robuste (FastAPI)
✅ Interface Premium Dark Mode
✅ Filtrage avancé et recherche
✅ Visualisations interactives (Plotly)
✅ Export CSV
✅ Tri multi-colonnes
✅ Profils joueurs détaillés


### 9.2 Défis Rencontrés

**Challenge 1 : Ambiguïté de Clés Étrangères (SQLAlchemy)**
- **Problème** : `AmbiguousForeignKeysError` lors des jointures Match-Team
- **Solution** : Spécification explicite des clés (`foreign_keys=[...]`)

**Challenge 2 : Injection Sécurisée de Données JavaScript**
- **Problème** : Conflit Jinja2 `{{ }}` vs JS `{ }`
- **Solution** : Utilisation de `|tojson|safe` dans des balises `<script type="application/json">`

**Challenge 3 : Performance des Requêtes Complexes**
- **Problème** : Agrégations lentes (> 2s) sur 10k perfs
- **Solution** : Indexation B-Tree + Eager Loading

**Challenge 4 : Tri Multi-Colonnes Côté Client**
- **Problème** : Freeze du navigateur avec 500+ rows
- **Solution** : Algorithme optimisé + DocumentFragment

### 9.3 Perspectives d'Évolution

#### Court Terme (1-3 mois)
- [ ] **Authentification** : JWT pour multi-utilisateurs
- [ ] **Favoris** : Sauvegarde de joueurs/équipes favoris
- [ ] **Comparateur** : Outil Head-to-Head de 2 joueurs
- [ ] **Export PDF** : Rapports imprimables

#### Moyen Terme (3-6 mois)
- [ ] **Machine Learning** : Prédiction de résultats (scikit-learn)
  - Modèle de régression pour xG
  - Classifier pour Win Probability
- [ ] **API Publique** : Endpoints RESTful pour développeurs tiers
- [ ] **Mobile App** : React Native companion app
- [ ] **Notifications** : Alertes sur performance (email/push)

#### Long Terme (6-12 mois)
- [ ] **Temps Réel** : WebSockets pour live scores
- [ ] **Video Analysis** : Intégration clips vidéo par match
- [ ] **Social Features** : Commentaires, partage de stats
- [ ] **Multi-Sport** : Extension Basketball, Rugby

### 9.4 Conclusion

Le projet **Atlas Performance** démontre la puissance d'une stack moderne (FastAPI + PostgreSQL + Tailwind) pour créer des applications Data-Intensive. 

**Points Forts :**
- Architecture modulaire et scalable
- Design professionnel et intuitif
- Performance optimisée

**Leçons Apprises :**
- Importance de l'indexation en BDD
- Validation stricte des données (Pydantic) évite beaucoup de bugs
- UX > Features : Mieux vaut 5 features polies que 20 buggées

**Impact :**
Ce projet pose les bases d'une véritable solution SaaS pour l'analytics football, potentiellement commercialisable auprès de clubs semi-professionnels et académies de formation.

---

*Atlas Performance Analytics v1.0*
