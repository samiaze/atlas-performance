# etl/transform/validators.py
from typing import Dict, Any, List, Tuple
from etl.utils.logger import log_warning, log_error, log_info

VALID_POSITIONS = {'Goalkeeper', 'Defender', 'Midfielder', 'Attacker', None}

def validate_match(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if data.get('date') is None: errors.append("Date manquante")
    if data['home_team_api_id'] == data['away_team_api_id']:
        errors.append(f"Équipes identiques (ID: {data['home_team_api_id']})")
    return len(errors) == 0, errors

def validate_player(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors = []
    if not data.get('name'): errors.append("Nom manquant")
    return len(errors) == 0, errors

def validate_performance(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valide et CORRIGE les incohérences mineures."""
    errors = []
    
    # Validation Note
    if data.get('rating') is not None:
        if not (0 <= data['rating'] <= 10):
            errors.append(f"Rating invalide: {data['rating']}")

    # Correction Auto : Tirs
    if data['shots_on_target'] > data['shots_total']:
        # On corrige au lieu de rejeter
        data['shots_on_target'] = data['shots_total']

    # Correction Auto : Passes (C'est ici que ça bloquait)
    if data['passes_accurate'] > data['passes_total']:
        # log_warning(f"Correction passes P{data['player_api_id']}: {data['passes_accurate']}/{data['passes_total']} -> {data['passes_total']}")
        data['passes_accurate'] = data['passes_total']

    return len(errors) == 0, errors

def validate_all_data(matches, players, performances):
    valid_matches = []
    valid_players = []
    valid_perfs = []
    
    for m in matches:
        is_valid, _ = validate_match(m)
        if is_valid: valid_matches.append(m)
            
    for p in players:
        is_valid, _ = validate_player(p)
        if is_valid: valid_players.append(p)

    for perf in performances:
        is_valid, errs = validate_performance(perf)
        if is_valid:
            valid_perfs.append(perf)
        else:
            log_error(f"Performance rejetée (P:{perf.get('player_api_id')}): {', '.join(errs)}")

    return valid_matches, valid_players, valid_perfs