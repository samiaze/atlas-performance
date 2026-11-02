# scripts/run_etl.ps1

Write-Host "[*] Lancement du Pipeline ETL AtlasPerformance..." -ForegroundColor Green

# 1. Vérifier si le conteneur tourne
if (-not (docker ps -q -f name=atlas_app)) {
    Write-Host "[!] [ERREUR] Le conteneur 'atlas_app' ne tourne pas." -ForegroundColor Red
    Write-Host "Veuillez lancer 'docker-compose up -d' d'abord."
    exit 1
}

# 2. Exécution du script Python dans le conteneur
# Note: On utilise 'cmd /c' pour s'assurer que docker-compose est bien interprété
docker-compose exec web python -m etl.run_etl --mode full

# 3. Récupération des statistiques avancées (Matchs)
Write-Host "[*] Recuperation des statistiques de matchs..." -ForegroundColor Cyan
docker-compose exec -T web python -m etl.fetch_match_stats

# 4. Recalcul des Notes Joueurs (Custom Algorithm)
Write-Host "[*] Recalcul des notes joueurs..." -ForegroundColor Cyan
docker-compose exec -T web python -m app.recalculate_ratings

Write-Host "[OK] Script termine." -ForegroundColor Green