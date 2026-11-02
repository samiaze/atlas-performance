from typing import List, Tuple
from datetime import date
from sqlalchemy.orm import Session
from app.schemas.performance import PerformanceCreate
from app.models import Performance

def validate_match_score(home_score: int, away_score: int) -> Tuple[bool, str]:
    """Vérifie que les scores sont positifs et réalistes."""
    if home_score < 0 or away_score < 0:
        return False, "Scores cannot be negative"
    if home_score > 30 or away_score > 30: # Limite de sécurité
        return False, "Score seems unrealistically high (>30)"
    return True, ""

def validate_performance_data(performance: PerformanceCreate) -> Tuple[bool, List[str]]:
    """
    Vérifie la cohérence statistique d'une performance.
    Retourne (is_valid, list_of_errors).
    """
    errors = []

    # 1. Validation Rating
    if performance.rating is not None and not (0 <= performance.rating <= 10):
        errors.append("Rating must be between 0 and 10")

    # 2. Validation Temps de jeu
    if not (0 <= performance.minutes_played <= 130): # 120 + temps add
        errors.append("Minutes played must be between 0 and 130")

    # 3. Cohérence Passes
    if performance.passes_accurate > performance.passes_total:
        errors.append(f"Accurate passes ({performance.passes_accurate}) cannot exceed total passes ({performance.passes_total})")

    # 4. Cohérence Tirs
    if performance.shots_on_target > performance.shots_total:
        errors.append(f"Shots on target ({performance.shots_on_target}) cannot exceed total shots ({performance.shots_total})")

    # 5. Cohérence Cartons
    if performance.yellow_cards > 2:
        errors.append("Cannot have more than 2 yellow cards")
    if performance.red_cards > 1:
        errors.append("Cannot have more than 1 red card")

    return len(errors) == 0, errors

def validate_player_age(birth_date: date) -> Tuple[bool, str]:
    """Vérifie si l'âge du joueur est cohérent pour un pro (15-50 ans)."""
    if not birth_date:
        return True, "" # Pas de date, pas de validation possible
        
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    if age < 15:
        return False, f"Player is too young ({age} years old)"
    if age > 50:
        return False, f"Player is too old ({age} years old)"
        
    return True, ""

def check_duplicate_performance(db: Session, player_id: int, match_id: int) -> bool:
    """Vérifie si une performance existe déjà pour ce couple joueur/match."""
    exists = db.query(Performance).filter(
        Performance.player_id == player_id,
        Performance.match_id == match_id
    ).first()
    return exists is not None