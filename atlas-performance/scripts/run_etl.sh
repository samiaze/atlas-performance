#!/bin/bash
# scripts/run_etl.sh

# Couleurs
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Lancement du Pipeline ETL AtlasPerformance...${NC}"

# Vérifier si le conteneur tourne
if [ ! "$(docker ps -q -f name=atlas_app)" ]; then
    echo "❌ Le conteneur 'atlas_app' ne tourne pas. Lancez 'docker-compose up -d' d'abord."
    exit 1
fi

# Exécution du script Python dans le conteneur
docker-compose exec web python -m etl.run_etl --mode full

# Récupération des statistiques avancées (Matchs)
docker-compose exec -T web python -m etl.fetch_match_stats

# Recalcul des Notes Joueurs (Custom Algorithm)
echo -e "${GREEN}🔄 Recalcul des notes joueurs...${NC}"
docker-compose exec web python -m app.recalculate_ratings

echo -e "${GREEN}🏁 Script terminé.${NC}"