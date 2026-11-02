from typing import Dict, Any, List, Optional
import re
from etl.utils.logger import log_warning

# Mapping des statuts API-Football vers notre modèle DB
STATUS_MAPPING = {
    # À venir
    'NS': 'scheduled', 'TBD': 'scheduled',
    # En cours
    '1H': 'live', 'HT': 'live', '2H': 'live', 'ET': 'live', 'P': 'live', 'BT': 'live',
    # Terminés
    'FT': 'finished', 'AET': 'finished', 'PEN': 'finished',
    # Annulés/Reportés
    'PST': 'postponed', 'CANC': 'cancelled', 'ABD': 'cancelled', 'AWD': 'finished', 'WO': 'finished'
}

# Normalisation des positions
POSITION_MAPPING = {
    'G': 'Goalkeeper', 'Goalkeeper': 'Goalkeeper',
    'D': 'Defender', 'Defender': 'Defender',
    'M': 'Midfielder', 'Midfielder': 'Midfielder',
    'F': 'Attacker', 'Attacker': 'Attacker'
}

def _clean_str(value: Any) -> Optional[str]:
    """Helper pour nettoyer les strings (strip)."""
    if isinstance(value, str):
        return value.strip()
    return None

def _safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Helper pour convertir en int sans crasher."""
    try:
        if value is None: return default
        return int(value)
    except (ValueError, TypeError):
        return default

def _safe_float(value: Any) -> Optional[float]:
    """Helper pour convertir en float (gère 'N/A' ou None)."""
    try:
        if value is None or value == 'N/A': return None
        return float(value)
    except (ValueError, TypeError):
        return None

# --- NETTOYAGE PAR ENTITÉ ---

def clean_competition_data(comp: Dict[str, Any]) -> Dict[str, Any]:
    # Support both flat and nested structures
    if 'league' in comp: # Raw API
        return {
            "api_id": comp['league']['id'],
            "name": _clean_str(comp['league']['name']),
            "season": _safe_int(comp['seasons'][0]['year']),
            "country": _clean_str(comp['country']['name']),
            "logo": _clean_str(comp['league']['logo'])
        }
        
    return {
        "api_id": comp.get('api_id'),
        "name": _clean_str(comp.get('name')),
        "season": _safe_int(comp.get('season')),
        "country": _clean_str(comp.get('country')),
        "logo": _clean_str(comp.get('logo'))
    }

def clean_team_data(team: Dict[str, Any]) -> Dict[str, Any]:
    # Cas 1: Structure imbriquée 'team' + 'venue' (API)
    if 'team' in team and 'venue' in team:
        return {
            "api_id": team['team']['id'],
            "name": _clean_str(team['team']['name']),
            "country": _clean_str(team['team']['country']),
            "logo": _clean_str(team['team']['logo']),
            "founded": _safe_int(team['team']['founded']),
            "venue_name": _clean_str(team['venue']['name']),
            "competition_api_id": team.get('competition_id')
        }
    
    # Cas 2: Déjà plat
    return {
        "api_id": team.get('api_id'),
        "name": _clean_str(team.get('name')),
        "country": _clean_str(team.get('country')),
        "logo": _clean_str(team.get('logo')),
        "founded": _safe_int(team.get('founded')),
        "venue_name": _clean_str(team.get('venue') or team.get('venue_name')),
        "competition_api_id": team.get('competition_api_id')
    }

def clean_match_data(match: Dict[str, Any]) -> Dict[str, Any]:
    # Raw API structure
    if 'fixture' in match:
        raw_status = match['fixture']['status']['short']
        clean_status = STATUS_MAPPING.get(raw_status, 'scheduled')
        return {
            "api_id": match['fixture']['id'],
            "date": match['fixture']['date'],
            "round": _clean_str(match['league']['round']),
            "status": clean_status,
            "venue": _clean_str(match['fixture']['venue']['name']),
            "home_team_api_id": match['teams']['home']['id'],
            "away_team_api_id": match['teams']['away']['id'],
            "home_score": _safe_int(match['goals']['home']),
            "away_score": _safe_int(match['goals']['away']),
            "competition_api_id": match['league']['id']
        }
        
    # Flat structure
    raw_status = match.get('status', 'NS')
    clean_status = STATUS_MAPPING.get(raw_status, 'scheduled')
    return {
        "api_id": match.get('api_id'),
        "date": match.get('date'),
        "round": _clean_str(match.get('round')),
        "status": clean_status,
        "venue": _clean_str(match.get('venue')),
        "home_team_api_id": match.get('home_team_api_id'),
        "away_team_api_id": match.get('away_team_api_id'),
        "home_score": _safe_int(match.get('home_score')),
        "away_score": _safe_int(match.get('away_score')),
        "competition_api_id": match.get('competition_api_id')
    }

def clean_player_data(player: Dict[str, Any]) -> Dict[str, Any]:
    # Normalisation Position
    raw_pos = player.get('position')
    clean_pos = POSITION_MAPPING.get(raw_pos, raw_pos)
    
    # Regex pour nettoyer taille/poids
    height = None
    if player.get('height') and isinstance(player['height'], str):
        matches = re.findall(r'\d+', player['height'])
        if matches: height = int(matches[0])
    
    weight = None
    if player.get('weight') and isinstance(player['weight'], str):
        matches = re.findall(r'\d+', player['weight'])
        if matches: weight = int(matches[0])

    return {
        "api_id": player.get('api_id') or player.get('id'),
        "name": _clean_str(player.get('name')),
        "firstname": _clean_str(player.get('firstname')),
        "lastname": _clean_str(player.get('lastname')),
        "age": _safe_int(player.get('age')),
        "birth_date": player.get('birth_date'),
        "nationality": _clean_str(player.get('nationality')),
        "height": height or _clean_str(player.get('height')),
        "weight": weight or _clean_str(player.get('weight')),
        "photo": _clean_str(player.get('photo')),
        "position": clean_pos,
        "number": _safe_int(player.get('number')),
        "team_api_id": player.get('team_api_id') or player.get('team', {}).get('id')
    }

def clean_performance_data(perf: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "player_api_id": perf.get('player_api_id'),
        "match_api_id": perf.get('match_api_id'),
        "team_api_id": perf.get('team_api_id'),
        "rating": _safe_float(perf.get('rating')),
        # Ints avec défaut à 0
        "minutes_played": _safe_int(perf.get('minutes_played'), 0),
        "goals": _safe_int(perf.get('goals'), 0),
        "assists": _safe_int(perf.get('assists'), 0),
        "shots_total": _safe_int(perf.get('shots_total'), 0),
        "shots_on_target": _safe_int(perf.get('shots_on_target'), 0),
        "passes_total": _safe_int(perf.get('passes_total'), 0),
        "passes_accurate": _safe_int(perf.get('passes_accurate'), 0),
        "tackles": _safe_int(perf.get('tackles'), 0),
        "interceptions": _safe_int(perf.get('interceptions'), 0),
        "fouls_committed": _safe_int(perf.get('fouls_committed'), 0),
        "fouls_drawn": _safe_int(perf.get('fouls_drawn'), 0),
        "yellow_cards": _safe_int(perf.get('yellow_cards'), 0),
        "red_cards": _safe_int(perf.get('red_cards'), 0),
        "saves": _safe_int(perf.get('saves'), 0)
    }