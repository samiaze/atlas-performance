from typing import List, Optional, Dict, Any
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from app.database import get_db
from app.models import Match, Team, Performance
from app.schemas.match import MatchCreate, MatchUpdate, MatchResponse, MatchWithDetails
from app.schemas.performance import PerformanceResponse

router = APIRouter()

@router.get("/", response_model=List[MatchResponse], summary="Lister les matchs (Filtres avancés)")
def read_matches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    competition_id: Optional[int] = None,
    team_id: Optional[int] = Query(None, description="Matchs d'une équipe (Domicile OU Extérieur)"),
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Récupère les matchs selon plusieurs critères cumulatifs.
    Tri par défaut : Date décroissante (le plus récent en premier).
    """
    query = db.query(Match)

    if competition_id:
        query = query.filter(Match.competition_id == competition_id)
    
    if team_id:
        # On cherche l'équipe soit en Home, soit en Away
        query = query.filter(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
    
    if status_filter:
        query = query.filter(Match.status == status_filter)

    if date_from:
        query = query.filter(Match.date >= date_from)
    
    if date_to:
        query = query.filter(Match.date <= date_to)

    # Tri par date DESC
    matches = query.order_by(Match.date.desc()).offset(skip).limit(limit).all()
    return matches

@router.get("/{match_id}", response_model=MatchWithDetails, summary="Détail d'un match complet")
def read_match(match_id: int, db: Session = Depends(get_db)):
    """
    Récupère un match avec les objets complets des équipes (Home/Away).
    Utilise joinedload pour éviter les requêtes N+1.
    """
    match = db.query(Match).options(
        joinedload(Match.home_team),
        joinedload(Match.away_team)
    ).filter(Match.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

@router.get("/{match_id}/performances", response_model=List[PerformanceResponse], summary="Performances du match")
def read_match_performances(match_id: int, db: Session = Depends(get_db)):
    """Récupère toutes les stats individuelles des joueurs pour ce match."""
    # Vérif existance match
    if not db.query(Match).filter(Match.id == match_id).first():
        raise HTTPException(status_code=404, detail="Match not found")
        
    perfs = db.query(Performance).filter(Performance.match_id == match_id).all()
    return perfs

@router.get("/{match_id}/statistics", response_model=Dict[str, Any], summary="Stats agrégées par équipe")
def read_match_statistics(match_id: int, db: Session = Depends(get_db)):
    """
    Calcule les stats globales du match (Tirs, Passes, Buts) en agrégeant les perfs des joueurs.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Fonction helper pour agréger
    def get_team_stats(team_id):
        stats = db.query(
            func.sum(Performance.goals).label("goals"),
            func.sum(Performance.shots_total).label("shots"),
            func.sum(Performance.shots_on_target).label("shots_on_target"),
            func.sum(Performance.passes_total).label("passes"),
            func.avg(Performance.rating).label("avg_rating")
        ).join(Performance.player)\
         .filter(Performance.match_id == match_id, Performance.player.has(team_id=team_id))\
         .first()
         
        return {
            "goals": stats.goals or 0,
            "shots": stats.shots or 0,
            "shots_on_target": stats.shots_on_target or 0,
            "passes": stats.passes or 0,
            "avg_rating": round(stats.avg_rating, 2) if stats.avg_rating else 0.0
        }

    return {
        "home": get_team_stats(match.home_team_id),
        "away": get_team_stats(match.away_team_id)
    }

# --- CRUD STANDARD ---

@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    if db.query(Match).filter(Match.id == match.id).first():
        raise HTTPException(status_code=409, detail="Match ID already exists")
    db_match = Match(**match.model_dump())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

@router.put("/{match_id}", response_model=MatchResponse)
def update_match(match_id: int, match_update: MatchUpdate, db: Session = Depends(get_db)):
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match not found")
    for k, v in match_update.model_dump(exclude_unset=True).items():
        setattr(db_match, k, v)
    db.commit()
    db.refresh(db_match)
    return db_match

@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(match_id: int, db: Session = Depends(get_db)):
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if not db_match:
        raise HTTPException(status_code=404, detail="Match not found")
    db.delete(db_match)
    db.commit()
    return None