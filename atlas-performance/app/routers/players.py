from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.database import get_db
from app.models import Player, Performance, Match
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerResponse, PlayerWithStats
from app.schemas.performance import PerformanceResponse

router = APIRouter()

@router.get("/", response_model=List[PlayerResponse], summary="Lister les joueurs")
def read_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    team_id: Optional[int] = None,
    position: Optional[str] = None,
    search: Optional[str] = Query(None, description="Recherche par nom (ILIKE)"),
    min_rating: Optional[float] = None, # Ce filtre est complexe car le rating est dans Performance
    db: Session = Depends(get_db)
):
    query = db.query(Player).options(joinedload(Player.team))

    if team_id:
        query = query.filter(Player.team_id == team_id)
    
    if position:
        query = query.filter(Player.position == position)
    
    if search:
        query = query.filter(Player.name.ilike(f"%{search}%"))

    # Note: Filtrer par rating moyen ici serait très lourd. 
    # On le fait généralement sur l'endpoint analytics ou via une sous-requête.
    
    return query.offset(skip).limit(limit).all()

@router.get("/{player_id}", response_model=PlayerWithStats, summary="Joueur avec stats globales")
def read_player(player_id: int, db: Session = Depends(get_db)):
    """
    Récupère le joueur et calcule ses stats totales (Buts, Passes, Note Moyenne).
    """
    player = db.query(Player).options(joinedload(Player.team)).filter(Player.id == player_id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Agrégation SQL pour performance
    stats = db.query(
        func.count(Performance.id).label("matches"),
        func.sum(Performance.goals).label("goals"),
        func.sum(Performance.assists).label("assists"),
        func.avg(Performance.rating).label("avg_rating")
    ).filter(Performance.player_id == player_id).first()

    # Transformation en Pydantic Schema
    # On crée une copie des données du joueur et on injecte les stats
    player_data = PlayerWithStats.model_validate(player)
    player_data.total_matches = stats.matches or 0
    player_data.total_goals = stats.goals or 0
    player_data.total_assists = stats.assists or 0
    player_data.average_rating = round(stats.avg_rating, 2) if stats.avg_rating else 0.0

    return player_data

@router.get("/{player_id}/performances", response_model=List[PerformanceResponse], summary="Historique des matchs")
def read_player_performances(
    player_id: int, 
    limit: int = 20,
    sort_by: str = Query("date", regex="^(date|rating)$"),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des performances d'un joueur.
    """
    if not db.query(Player).filter(Player.id == player_id).first():
        raise HTTPException(status_code=404, detail="Player not found")

    query = db.query(Performance).filter(Performance.player_id == player_id)

    # Jointure nécessaire pour trier par date de match
    if sort_by == "date":
        query = query.join(Match).order_by(Match.date.desc())
    elif sort_by == "rating":
        query = query.order_by(Performance.rating.desc())

    return query.limit(limit).all()

@router.get("/{player_id}/statistics", response_model=Dict[str, float], summary="KPIs détaillés")
def read_player_statistics(player_id: int, db: Session = Depends(get_db)):
    """
    Retourne un dictionnaire de toutes les moyennes (pour les graphiques Radar).
    """
    stats = db.query(
        func.avg(Performance.goals).label("avg_goals"),
        func.avg(Performance.assists).label("avg_assists"),
        func.avg(Performance.shots_on_target).label("avg_shots_target"),
        func.avg(Performance.passes_accurate).label("avg_passes"),
        func.avg(Performance.tackles).label("avg_tackles"),
        func.avg(Performance.interceptions).label("avg_interceptions"),
        func.avg(Performance.rating).label("avg_rating")
    ).filter(Performance.player_id == player_id).first()

    if not stats or not stats.avg_rating:
        return {"avg_rating": 0.0}

    return {k: round(v, 2) if v else 0.0 for k, v in stats._mapping.items()}

# --- CRUD STANDARD ---

@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    if db.query(Player).filter(Player.id == player.id).first():
        raise HTTPException(status_code=409, detail="Player ID exists")
    db_player = Player(**player.model_dump())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(player_id: int, player_update: PlayerUpdate, db: Session = Depends(get_db)):
    db_player = db.query(Player).filter(Player.id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    for k, v in player_update.model_dump(exclude_unset=True).items():
        setattr(db_player, k, v)
    db.commit()
    db.refresh(db_player)
    return db_player

@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int, db: Session = Depends(get_db)):
    db_player = db.query(Player).filter(Player.id == player_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
    db.delete(db_player)
    db.commit()
    return None