from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Performance, Player, Match
from app.schemas.performance import PerformanceCreate, PerformanceUpdate, PerformanceResponse

router = APIRouter()

@router.get("/", response_model=List[PerformanceResponse], summary="Explorer les performances brutes")
def read_performances(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    player_id: Optional[int] = None,
    match_id: Optional[int] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=10),
    db: Session = Depends(get_db)
):
    query = db.query(Performance)

    if player_id:
        query = query.filter(Performance.player_id == player_id)
    if match_id:
        query = query.filter(Performance.match_id == match_id)
    if min_rating:
        query = query.filter(Performance.rating >= min_rating)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{performance_id}", response_model=PerformanceResponse, summary="Détail d'une perf")
def read_performance(performance_id: int, db: Session = Depends(get_db)):
    perf = db.query(Performance).filter(Performance.id == performance_id).first()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    return perf

@router.post("/", response_model=PerformanceResponse, status_code=status.HTTP_201_CREATED)
def create_performance(perf: PerformanceCreate, db: Session = Depends(get_db)):
    # Vérifier intégrité référentielle
    if not db.query(Player).filter(Player.id == perf.player_id).first():
        raise HTTPException(status_code=404, detail="Player not found")
    if not db.query(Match).filter(Match.id == perf.match_id).first():
        raise HTTPException(status_code=404, detail="Match not found")

    # Vérifier doublon (Un joueur n'a qu'une perf par match)
    existing = db.query(Performance).filter(
        Performance.player_id == perf.player_id,
        Performance.match_id == perf.match_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Performance already exists for this player/match")

    db_perf = Performance(**perf.model_dump())
    db.add(db_perf)
    db.commit()
    db.refresh(db_perf)
    return db_perf

@router.put("/{performance_id}", response_model=PerformanceResponse)
def update_performance(performance_id: int, perf_update: PerformanceUpdate, db: Session = Depends(get_db)):
    db_perf = db.query(Performance).filter(Performance.id == performance_id).first()
    if not db_perf:
        raise HTTPException(status_code=404, detail="Performance not found")
        
    for k, v in perf_update.model_dump(exclude_unset=True).items():
        setattr(db_perf, k, v)
        
    db.commit()
    db.refresh(db_perf)
    return db_perf

@router.delete("/{performance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_performance(performance_id: int, db: Session = Depends(get_db)):
    db_perf = db.query(Performance).filter(Performance.id == performance_id).first()
    if not db_perf:
        raise HTTPException(status_code=404, detail="Performance not found")
    db.delete(db_perf)
    db.commit()
    return None