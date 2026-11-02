from typing import Dict, List, Optional
from pydantic import BaseModel

class DashboardSummary(BaseModel):
    """Résumé global pour la page d'accueil."""
    total_competitions: int
    total_teams: int
    total_matches: int
    total_players: int
    total_goals_scored: int

class TopScorer(BaseModel):
    """Structure pour le classement des buteurs."""
    player_id: int
    name: str
    team_name: str
    total_goals: int
    matches_played: int
    goals_per_match: float

class TeamStats(BaseModel):
    """Stats agrégées pour une équipe."""
    team_id: int
    name: str
    goals_for: int
    goals_against: int
    clean_sheets: int
    avg_possession: Optional[float] = None

class PlayerComparison(BaseModel):
    """Comparaison Radar entre deux joueurs."""
    player1: Dict[str, float]
    player2: Dict[str, float]
    labels: List[str]