from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, case
from app.models import Performance, Match, Player, Team, Competition

# --- FONCTIONS DASHBOARD & GLOBAL ---

def get_dashboard_counts(db: Session):
    """Récupère les compteurs globaux pour le dashboard."""
    return {
        "competitions": db.query(Competition).count(),
        "teams": db.query(Team).count(),
        "matches": db.query(Match).count(),
        "players": db.query(Player).count(),
        "goals_scored": db.query(func.sum(Match.home_score) + func.sum(Match.away_score)).scalar() or 0
    }

# --- FONCTIONS ÉQUIPE ---

def calculate_team_stats(db: Session, team_id: int):
    """
    Calcule les statistiques avancées d'une équipe :
    - Victoires / Nuls / Défaites
    - Buts Marqués / Encaissés
    - Cartons
    """
    # On récupère tous les matchs terminés de l'équipe
    matches = db.query(Match).filter(
        or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
        Match.status.in_(['FT', 'AET', 'PEN']) # Matchs terminés uniquement
    ).all()

    stats = {
        "played": 0, "wins": 0, "draws": 0, "losses": 0,
        "goals_for": 0, "goals_against": 0,
        "clean_sheets": 0
    }

    for m in matches:
        stats["played"] += 1
        is_home = m.home_team_id == team_id
        
        score_team = m.home_score if is_home else m.away_score
        score_opp = m.away_score if is_home else m.home_score

        stats["goals_for"] += score_team
        stats["goals_against"] += score_opp

        if score_opp == 0:
            stats["clean_sheets"] += 1

        if score_team > score_opp:
            stats["wins"] += 1
        elif score_team == score_opp:
            stats["draws"] += 1
        else:
            stats["losses"] += 1

    # Calcul ratio victoire
    stats["win_rate"] = round((stats["wins"] / stats["played"] * 100), 2) if stats["played"] > 0 else 0.0
    
    # Agrégation des cartons via la table Performance
    cards = db.query(
        func.sum(Performance.yellow_cards).label('yellow'),
        func.sum(Performance.red_cards).label('red')
    ).join(Player).filter(Player.team_id == team_id).first()

    stats["yellow_cards"] = cards.yellow or 0
    stats["red_cards"] = cards.red or 0

    return stats

def calculate_team_win_rate(db: Session, team_id: int) -> float:
    """Calcule le pourcentage de victoire d'une équipe (Wrapper simple)."""
    stats = calculate_team_stats(db, team_id)
    return stats["win_rate"]

def get_team_form(db: Session, team_id: int, last_n: int = 5) -> List[str]:
    """
    Retourne la forme de l'équipe sur les N derniers matchs.
    Format : ['W', 'D', 'L', 'W', 'W'] (Du plus récent au plus ancien)
    """
    matches = db.query(Match).filter(
        or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
        Match.status.in_(['FT', 'AET', 'PEN'])
    ).order_by(Match.date.desc()).limit(last_n).all()

    form = []
    for m in matches:
        is_home = m.home_team_id == team_id
        goals_for = m.home_score if is_home else m.away_score
        goals_against = m.away_score if is_home else m.home_score

        if goals_for > goals_against:
            form.append('W') # Win
        elif goals_for == goals_against:
            form.append('D') # Draw
        else:
            form.append('L') # Loss
            
    return form

# --- FONCTIONS JOUEUR ---

def calculate_player_average_rating(db: Session, player_id: int) -> float:
    """Calcule la note moyenne d'un joueur sur toute sa carrière."""
    result = db.query(func.avg(Performance.rating)).filter(
        Performance.player_id == player_id,
        Performance.rating.isnot(None)
    ).scalar()
    return round(result, 2) if result else 0.0

def get_player_best_performance(db: Session, player_id: int) -> Optional[Performance]:
    """Retourne la performance avec la note la plus élevée."""
    return db.query(Performance).filter(
        Performance.player_id == player_id,
        Performance.rating.isnot(None)
    ).order_by(Performance.rating.desc()).first()

def calculate_player_consistency(db: Session, player_id: int) -> float:
    """
    Calcule l'écart-type (Standard Deviation) des notes d'un joueur.
    """
    ratings = [r[0] for r in db.query(Performance.rating).filter(
        Performance.player_id == player_id, Performance.rating.isnot(None)
    ).all()]
    
    if len(ratings) < 2: return 0.0
    
    import statistics
    return round(statistics.stdev(ratings), 2)

# --- FONCTIONS PRÉDICTIVES ---

def predict_match_outcome(db: Session, match_id: int):
    """
    Algorithme heuristique simple de prédiction basé sur le taux de victoire.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        return None

    home_stats = calculate_team_stats(db, match.home_team_id)
    away_stats = calculate_team_stats(db, match.away_team_id)

    # Poids arbitraires pour l'exemple
    home_strength = home_stats['win_rate'] + 5 # Avantage domicile
    away_strength = away_stats['win_rate']

    total = home_strength + away_strength + 20 # Marge pour match nul

    prob_home = round((home_strength / total) * 100, 1) if total > 0 else 33.3
    prob_away = round((away_strength / total) * 100, 1) if total > 0 else 33.3
    prob_draw = round(100 - prob_home - prob_away, 1)

    return {
        "match_id": match_id,
        "home_team": match.home_team.name,
        "away_team": match.away_team.name,
        "probabilities": {
            "home_win": prob_home,
            "draw": prob_draw,
            "away_win": prob_away
        },
        "factors": {
            "home_win_rate": home_stats['win_rate'],
            "away_win_rate": away_stats['win_rate']
        }
    }