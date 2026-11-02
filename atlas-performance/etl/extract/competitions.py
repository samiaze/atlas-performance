from typing import List, Dict, Any, Optional
from etl.config import COMPETITIONS
from etl.utils.http_client import api_client
from etl.utils.logger import log_info, log_error, log_success

def fetch_competition(league_id: int, season: int) -> Optional[Dict[str, Any]]:
    """
    Récupère les détails d'une compétition depuis l'API.
    Endpoint: /leagues
    """
    log_info(f"Extraction compétition ID: {league_id}, Saison: {season}")
    
    data = api_client.get("leagues", params={"id": league_id, "season": season})
    
    if not data:
        log_error(f"Aucune donnée trouvée pour la compétition {league_id}")
        return None

    try:
        # L'API renvoie une liste, on prend le premier élément
        item = data[0]
        league = item['league']
        country = item['country']
        
        return {
            "api_id": league['id'],
            "name": league['name'],
            "season": season,
            "country": country['name'],
            "logo": league['logo']
        }
    except (IndexError, KeyError) as e:
        log_error(f"Erreur de parsing compétition: {e}")
        return None

def fetch_all_competitions() -> List[Dict[str, Any]]:
    """Récupère toutes les compétitions définies dans la config."""
    results = []
    for key, conf in COMPETITIONS.items():
        comp = fetch_competition(conf['id'], conf['season'])
        if comp:
            results.append(comp)
    
    log_success(f"{len(results)} compétitions extraites avec succès.")
    return results