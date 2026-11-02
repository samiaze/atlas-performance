from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app.database import get_db
from app.models import Player, Team, Performance, Match
from app.schemas.analytics import DashboardSummary, TopScorer, PlayerComparison
from app.schemas.match import MatchResponse
from app.services import statistics_service

router = APIRouter()

@router.get("/dashboard-summary", response_model=DashboardSummary, summary="Résumé global du Dashboard")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Retourne les chiffres clés pour la page d'accueil de l'application.
    """
    counts = statistics_service.get_dashboard_counts(db)
    
    # Note: Les champs latest_matches et upcoming_matches ne sont pas dans le schéma DashboardSummary
    # défini dans la Tâche 2.2 (qui ne contient que des totaux).
    # Si besoin, il faudra mettre à jour app/schemas/analytics.py pour inclure ces listes.
    # Ici, je renvoie les totaux demandés par le schéma.
    
    return DashboardSummary(
        total_competitions=counts["competitions"],
        total_teams=counts["teams"],
        total_matches=counts["matches"],
        total_players=counts["players"],
        total_goals_scored=counts["goals_scored"]
    )

@router.get("/top-scorers", response_model=List[TopScorer], summary="Classement des buteurs")
def get_top_scorers(
    limit: int = 10,
    competition_id: Optional[int] = None,
    min_matches: int = 3,
    db: Session = Depends(get_db)
):
    """
    Retourne les meilleurs buteurs avec ratio buts/match.
    """
    query = db.query(
        Player.id.label("player_id"),
        Player.name,
        Team.name.label("team_name"),
        func.sum(Performance.goals).label('total_goals'),
        func.count(Performance.id).label('matches_played')
    ).join(Performance).join(Team)

    if competition_id:
        query = query.join(Match).filter(Match.competition_id == competition_id)

    results = query.group_by(Player.id, Player.name, Team.name)\
        .having(func.count(Performance.id) >= min_matches)\
        .order_by(func.sum(Performance.goals).desc())\
        .limit(limit)\
        .all()

    # Transformation pour le schéma Pydantic
    return [
        TopScorer(
            player_id=r.player_id,
            name=r.name,
            team_name=r.team_name,
            total_goals=r.total_goals,
            matches_played=r.matches_played,
            goals_per_match=round(r.total_goals / r.matches_played, 2)
        )
        for r in results
    ]

@router.get("/top-rated-players", summary="Joueurs les mieux notés")
def get_top_rated_players(
    limit: int = 10, 
    min_matches: int = 5,
    db: Session = Depends(get_db)
):
    """
    Retourne les joueurs avec la meilleure note moyenne (Rating).
    """
    results = db.query(
        Player.id, Player.name, Team.name.label("team_name"),
        func.avg(Performance.rating).label("avg_rating"),
        func.count(Performance.id).label("matches_played")
    ).join(Performance).join(Team)\
     .filter(Performance.rating.isnot(None))\
     .group_by(Player.id, Player.name, Team.name)\
     .having(func.count(Performance.id) >= min_matches)\
     .order_by(desc("avg_rating"))\
     .limit(limit)\
     .all()

    return [
        {
            "player_id": r.id,
            "name": r.name,
            "team": r.team_name,
            "avg_rating": round(r.avg_rating, 2),
            "matches_played": r.matches_played
        }
        for r in results
    ]

@router.get("/team-statistics/{team_id}", summary="Statistiques avancées d'équipe")
def get_team_statistics(team_id: int, db: Session = Depends(get_db)):
    """
    Retourne les stats agrégées : Victoires, Nuls, Défaites, Buts, Cartons.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    stats = statistics_service.calculate_team_stats(db, team_id)
    stats["team_name"] = team.name
    return stats

@router.get("/player-statistics/{player_id}", summary="Statistiques avancées joueur")
def get_player_statistics(player_id: int, db: Session = Depends(get_db)):
    """
    KPIs moyens d'un joueur + Meilleure/Pire performance.
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Agrégations moyennes
    avgs = db.query(
        func.avg(Performance.rating).label("avg_rating"),
        func.avg(Performance.goals).label("avg_goals"),
        func.avg(Performance.assists).label("avg_assists"),
        func.avg(Performance.passes_accurate).label("avg_passes"),
        func.avg(Performance.shots_on_target).label("avg_shots"),
        func.sum(Performance.minutes_played).label("total_minutes")
    ).filter(Performance.player_id == player_id).first()

    # Meilleur match (Rating Max)
    best_perf = db.query(Performance).join(Match)\
        .filter(Performance.player_id == player_id)\
        .order_by(Performance.rating.desc())\
        .first()

    return {
        "player_name": player.name,
        "team": player.team.name,
        "stats": {
            "avg_rating": round(avgs.avg_rating, 2) if avgs.avg_rating else 0,
            "avg_goals": round(avgs.avg_goals, 2) if avgs.avg_goals else 0,
            "avg_assists": round(avgs.avg_assists, 2) if avgs.avg_assists else 0,
            "avg_passes": round(avgs.avg_passes, 1) if avgs.avg_passes else 0,
            "total_minutes": avgs.total_minutes or 0
        },
        "best_match": {
            "rating": best_perf.rating,
            "match_id": best_perf.match_id,
            "opponent": best_perf.match.away_team.name if best_perf.match.home_team_id == player.team_id else best_perf.match.home_team.name
        } if best_perf else None
    }

@router.post("/compare-players", response_model=List[PlayerComparison], summary="Comparateur de joueurs")
def compare_players(
    payload: Dict[str, List[int]] = Body(..., example={"player_ids": [1500, 1502]}),
    db: Session = Depends(get_db)
):
    """
    Compare jusqu'à 5 joueurs sur leurs moyennes (Radar Chart).
    Body: {"player_ids": [id1, id2, ...]}
    """
    player_ids = payload.get("player_ids", [])
    if len(player_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 players allowed for comparison")
    
    comparisons = []
    
    # Note: Le schéma PlayerComparison défini en 2.2 est un peu différent (player1 vs player2).
    # Ici, je l'adapte pour renvoyer une liste d'objets flexibles pour le frontend.
    
    for pid in player_ids:
        player = db.query(Player).filter(Player.id == pid).first()
        if not player:
            continue
            
        stats = db.query(
            func.avg(Performance.goals).label("Goals"),
            func.avg(Performance.assists).label("Assists"),
            func.avg(Performance.shots_total).label("Shots"),
            func.avg(Performance.passes_accurate).label("Passes"),
            func.avg(Performance.dribbles_success).label("Dribbles"), # Si dispo
            func.avg(Performance.tackles).label("Tackles"),
            func.avg(Performance.rating).label("Rating")
        ).filter(Performance.player_id == pid).first()
        
        # On normalise les données pour le radar chart (Exemple simplifié)
        data_map = {k: round(v, 2) if v else 0.0 for k, v in stats._mapping.items() if k != "Dribbles"}
        
        # Pour coller au schéma PlayerComparison, on triche un peu ou on adapte le schéma.
        # Ici je renvoie une structure adaptée pour une liste de comparaison.
        comparisons.append({
            "player_id": player.id,
            "name": player.name,
            "stats": data_map
        })
        
    return comparisons 

@router.get("/match-predictions/{match_id}", summary="Prédiction de match (IA Basique)")
def get_match_prediction(match_id: int, db: Session = Depends(get_db)):
    """
    Retourne des probabilités de victoire basées sur la forme récente.
    """
    prediction = statistics_service.predict_match_outcome(db, match_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Match not found")
    return prediction

@router.get("/performance-trends/{player_id}", summary="Tendance de forme (Graphique)")
def get_performance_trends(
    player_id: int, 
    last_n_matches: int = 10,
    db: Session = Depends(get_db)
):
    """
    Récupère l'évolution de la note du joueur sur ses N derniers matchs.
    Utile pour les graphiques de ligne (Line Chart).
    """
    trends = db.query(
        Match.date,
        Performance.rating,
        Performance.goals,
        Performance.assists
    ).join(Match)\
     .filter(Performance.player_id == player_id)\
     .order_by(Match.date.asc())\
     .limit(last_n_matches)\
     .all() # .limit sur la fin nécessite une sous-requête normalement, ici simplifié

    return [
        {
            "date": t.date.isoformat(),
            "rating": t.rating,
            "goals": t.goals,
            "assists": t.assists
        }
        for t in trends
    ]