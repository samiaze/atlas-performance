from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Team, Player, Match
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse, TeamWithPlayers
from app.schemas.player import PlayerResponse
from app.schemas.match import MatchResponse

router = APIRouter()

# --- ROUTES DE BASE (CRUD ÉQUIPE) ---

@router.get("/", response_model=List[TeamResponse], summary="Lister les équipes")
def read_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    competition_id: Optional[int] = Query(None, description="Filtrer par compétition"),
    search: Optional[str] = Query(None, description="Recherche par nom d'équipe (insensible à la casse)"),
    db: Session = Depends(get_db)
):
    query = db.query(Team)
    
    if competition_id:
        query = query.filter(Team.competition_api_id == competition_id)
    
    if search:
        # Recherche flexible (LIKE %search%)
        query = query.filter(Team.name.ilike(f"%{search}%"))
        
    return query.offset(skip).limit(limit).all()

@router.get("/{team_id}", response_model=TeamWithPlayers, summary="Détails complets d'une équipe")
def read_team(team_id: int, db: Session = Depends(get_db)):
    """
    Récupère une équipe et la liste de ses joueurs.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    if db.query(Team).filter(Team.id == team.id).first():
        raise HTTPException(status_code=409, detail="Team with this ID already exists")
    
    db_team = Team(**team.model_dump())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

@router.put("/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, team_update: TeamUpdate, db: Session = Depends(get_db)):
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    for k, v in team_update.model_dump(exclude_unset=True).items():
        setattr(db_team, k, v)
    
    db.commit()
    db.refresh(db_team)
    return db_team

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    db.delete(db_team)
    db.commit()
    return None

# --- ROUTES ASSOCIÉES (JOUEURS & MATCHS) ---

@router.get("/{team_id}/players", response_model=List[PlayerResponse], summary="Joueurs d'une équipe")
def read_team_players(team_id: int, db: Session = Depends(get_db)):
    """
    Récupère uniquement la liste des joueurs de l'équipe spécifiée.
    """
    # Vérifier d'abord si l'équipe existe
    if not db.query(Team).filter(Team.id == team_id).first():
        raise HTTPException(status_code=404, detail="Team not found")
        
    players = db.query(Player).filter(Player.team_id == team_id).all()
    return players

@router.get("/{team_id}/matches", response_model=List[MatchResponse], summary="Matchs d'une équipe")
def read_team_matches(
    team_id: int, 
    status_filter: Optional[str] = Query(None, alias="status", description="Filtrer par statut (ex: FT, NS)"),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les matchs (Domicile ET Extérieur) impliquant cette équipe.
    """
    if not db.query(Team).filter(Team.id == team_id).first():
        raise HTTPException(status_code=404, detail="Team not found")

    # Requête complexe avec OR (Domicile OU Extérieur)
    query = db.query(Match).filter(
        or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
    )
    
    if status_filter:
        query = query.filter(Match.status == status_filter)
        
    return query.order_by(Match.date.desc()).all()