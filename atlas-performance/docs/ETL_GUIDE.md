# 🔄 Guide du Pipeline ETL

Le module ETL (**Extract, Transform, Load**) est responsable de l'alimentation de la base de données PostgreSQL à partir de l'API externe (API-Football).

## 🛠️ Fonctionnement

Le pipeline se déroule en deux phases majeures, orchestrées par le script `scripts/run_etl.ps1`.

### Phase 1 : Données Structurelles (`etl.run_etl`)

Cette phase s'exécute via la commande `python -m etl.run_etl --mode full` dans le conteneur.

1.  **Extraction (`extract/`)** :
    *   Récupère les **Compétitions** configurées (Config dans `etl/config.py`).
    *   Récupère les **Équipes** participantes.
    *   Récupère tous les **Matchs** (Calendrier et Résultats).
    *   Récupère les **Joueurs** et leurs statistiques de performance par match.
    *   *Note : Utilise un système de cache JSON (`data/raw_json/`) pour éviter de rappeler l'API inutilement.*

2.  **Transformation (`transform/`)** :
    *   Nettoyage des données (valeurs nulles, formats de dates).
    *   Standardisation des noms.
    *   Calculs intermédiaires.

3.  **Chargement (`load/`)** :
    *   Insertion en base de données via SQLAlchemy.
    *   Gestion des relations (Clés étrangères).

### Phase 2 : Statistiques Avancées (`etl.fetch_match_stats`)

Cette phase s'exécute via la commande `python -m etl.fetch_match_stats` dans le conteneur.

1.  **Ciblage** : Sélectionne uniquement les matchs **terminés** ("FT", "AET", "PEN") présents en base.
2.  **Extraction** : Appelle l'endpoint `/fixtures/statistics` pour chaque match.
3.  **Upsert** :
    *   Si les stats n'existent pas : **Création**.
    *   Si les stats existent déjà : **Mise à jour** (avec actualisation du champ `updated_at`).

---

## ⚙️ Configuration

Le fichier `etl/config.py` permet de définir les compétitions à suivre :

```python
COMPETITIONS_TO_FETCH = [
    {"id": 1, "season": 2022},  # World Cup
    {"id": 6, "season": 2023},  # Africa Cup of Nations
    # ...
]
```

## 📂 Gestion du Cache

Pour économiser votre quota API (100 appels/jour en gratuit), l'ETL stocke les réponses brutes dans :
*   `data/raw_json/` (Données générales)
*   `data/raw_json_StatistiqueMatches/` (Stats avancées)

Si vous souhaitez forcer un retéléchargement depuis l'API, vous pouvez supprimer les fichiers JSON correspondants dans ces dossiers.
