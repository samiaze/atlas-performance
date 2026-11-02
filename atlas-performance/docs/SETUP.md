# 🚀 Guide d'Installation et de Démarrage

Ce guide vous explique comment installer, configurer et lancer le projet **AtlasPerformance** sur votre machine locale.

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir installé :

1.  **Docker Desktop** (avec Docker Compose) : [Télécharger Docker](https://www.docker.com/products/docker-desktop/)
2.  **Git** : [Télécharger Git](https://git-scm.com/downloads)
3.  **Clé API-Football** (Gratuite) :
    *   Créer un compte sur [RapidAPI](https://rapidapi.com/api-sports/api/api-football).
    *   Souscrire au plan "Basic" (Gratuit, 100 requêtes/jour).
    *   Récupérer votre `X-RapidAPI-Key`.

---

## 🛠️ Installation

### 1. Cloner le Projet

Ouvrez votre terminal et exécutez :

```powershell
git clone https://github.com/badr-abba/atlasperformance.git
cd atlasperformance
```

### 2. Configuration de l'Environnement

Copiez le fichier d'exemple `.env.example` vers `.env` :

```powershell
copy .env.example .env
```
*(Sur Linux/Mac : `cp .env.example .env`)*

Éditez le fichier `.env` avec un éditeur de texte (Bloc-notes, VS Code...) et ajoutez votre clé API :

```ini
# .env
RAPIDAPI_KEY=votre_cle_api_ici_xxxxxxxxxxxxxxxxxxxxx
RAPIDAPI_HOST=api-football-v1.p.rapidapi.com

# Configuration Base de Données (Par défaut)
DB_USER=atlas_user
DB_PASSWORD=atlas_password
DB_NAME=atlasperformance
DB_HOST=atlas_db
DB_PORT=5432
```

---

## ▶️ Démarrage de l'Application

### 1. Lancer les Conteneurs

Utilisez Docker Compose pour construire et démarrer les services (Application Web, Base de Données, Admin) :

```powershell
docker-compose up -d --build
```

*   Attendez quelques secondes que les conteneurs soient prêts.
*   Vérifiez l'état avec `docker ps`.

### 2. Initialiser les Données (ETL)

La base de données est vide au démarrage. Vous devez lancer le pipeline ETL pour télécharger les compétitions, équipes, matchs et joueurs.

Exécutez le script d'automatisation fourni :

```powershell
.\scripts\run_etl.ps1
```

Ce script va :
1.  Vérifier que le conteneur tourne.
2.  Lancer l'extraction principale (Matchs, Équipes, Joueurs).
3.  Lancer, à la suite, la récupération des **Statistiques Avancées** (Tirs, Possession, etc.).

*(Note : Le téléchargement initial peut prendre quelques minutes selon votre connexion et les limites de l'API).*

---

## 🌐 Accès à l'Application

Une fois lancé :

*   **Dashboard Application** : [http://localhost:8000](http://localhost:8000)
*   **Documentation API (Swagger)** : [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Administration DB (pgAdmin)** : [http://localhost:5050](http://localhost:5050)
    *   *Email* : `admin@atlas.com`
    *   *Password* : `admin`

---

## 🛑 Arrêt

Pour arrêter l'application et libérer les ressources :

```powershell
docker-compose down
```
