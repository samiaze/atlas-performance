from typing import List, Dict, Any
from etl.utils.http_client import api_client
from etl.utils.logger import log_info, log_error, log_success

def fetch_teams_by_league(league_id: int, season: int) -> List[Dict[str, Any]]:
    """
    Récupère les équipes d'une ligue pour une saison.
    Endpoint: /teams
    """
    log_info(f"Extraction équipes pour Ligue {league_id}...")
    
    data = api_client.get("teams", params={"league": league_id, "season": season})
    
    if not data:
        return []

    cleaned_teams = []
    for item in data:
        try:
            team = item['team']
            venue = item['venue']
            
            cleaned_teams.append({
                "api_id": team['id'],
                "name": team['name'],
                "country": team['country'],
                "logo": team['logo'],
                "founded": team['founded'],
                "venue": venue['name'],
                "competition_api_id": league_id
            })
        except KeyError as e:
            log_error(f"Donnée équipe incomplète ignorée : {e}")
            continue

    log_success(f"{len(cleaned_teams)} équipes extraites pour la ligue {league_id}.")
    return cleaned_teams

def fetch_all_teams(competitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrège les équipes de toutes les compétitions fournies."""
    all_teams = []
    for comp in competitions:
        teams = fetch_teams_by_league(comp['api_id'], comp['season'])
        all_teams.extend(teams)
    return all_teams