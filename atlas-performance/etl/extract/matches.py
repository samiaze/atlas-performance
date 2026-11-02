from typing import List, Dict, Any
from datetime import datetime
from etl.utils.http_client import api_client
from etl.utils.logger import log_info, log_error, log_success

def fetch_matches_by_league(league_id: int, season: int) -> List[Dict[str, Any]]:
    """
    Récupère tous les matchs d'une ligue.
    Endpoint: /fixtures
    """
    log_info(f"Extraction matchs pour Ligue {league_id}...")
    
    data = api_client.get("fixtures", params={"league": league_id, "season": season})
    
    if not data:
        return []

    cleaned_matches = []
    for item in data:
        try:
            fixture = item['fixture']
            league = item['league']
            teams = item['teams']
            goals = item['goals']
            
            # Parsing ISO Date (ex: 2024-02-11T20:00:00+00:00)
            # .replace('Z', '+00:00') gère le format UTC standard si présent
            match_date = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))

            cleaned_matches.append({
                "api_id": fixture['id'],
                "date": match_date,
                "round": league.get('round'),
                "status": fixture['status']['short'], # FT, NS, PST...
                "venue": fixture['venue']['name'],
                "home_team_api_id": teams['home']['id'],
                "away_team_api_id": teams['away']['id'],
                "home_score": goals['home'],
                "away_score": goals['away'],
                "competition_api_id": league_id
            })
        except (KeyError, ValueError) as e:
            log_error(f"Erreur parsing match {item.get('fixture', {}).get('id')}: {e}")
            continue

    log_success(f"{len(cleaned_matches)} matchs extraits pour la ligue {league_id}.")
    return cleaned_matches

def fetch_all_matches(competitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrège les matchs de toutes les compétitions."""
    all_matches = []
    for comp in competitions:
        matches = fetch_matches_by_league(comp['api_id'], comp['season'])
        all_matches.extend(matches)
    return all_matches