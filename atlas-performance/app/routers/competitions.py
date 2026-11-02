from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Competition
from app.schemas.competition import (
    CompetitionCreate, 
    CompetitionUpdate, 
    CompetitionResponse
)

router = APIRouter()

@router.get("/", response_model=List[CompetitionResponse], summary="Lister les compétitions")
def read_competitions(
    skip: int = Query(0, description="Nombre d'éléments à sauter (pagination)"),
    limit: int = Query(100, description="Nombre d'éléments à récupérer"),
    season: Optional[int] = Query(None, description="Filtrer par année de saison"),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des compétitions avec pagination et filtre optionnel par saison.
    """
    query = db.query(Competition)
    
    if season:
        query = query.filter(Competition.season == season)
        
    competitions = query.offset(skip).limit(limit).all()
    return competitions

@router.get("/{competition_id}", response_model=CompetitionResponse, summary="Récupérer une compétition")
def read_competition(competition_id: int, db: Session = Depends(get_db)):
    """
    Récupère les détails d'une compétition spécifique par son ID.
    """
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    return competition

@router.post("/", response_model=CompetitionResponse, status_code=status.HTTP_201_CREATED, summary="Créer une compétition")
def create_competition(comp: CompetitionCreate, db: Session = Depends(get_db)):
    """
    Crée une nouvelle compétition.
    Vérifie d'abord si une compétition avec le même nom et la même saison existe déjà.
    """
    existing = db.query(Competition).filter(
        Competition.name == comp.name, 
        Competition.season == comp.season
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409, 
            detail=f"Competition '{comp.name}' for season {comp.season} already exists."
        )
    
    # Création de l'objet ORM
    db_comp = Competition(**comp.model_dump())
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.put("/{competition_id}", response_model=CompetitionResponse, summary="Mettre à jour une compétition")
def update_competition(competition_id: int, comp_update: CompetitionUpdate, db: Session = Depends(get_db)):
    """
    Met à jour partiellement une compétition existante.
    """
    db_comp = db.query(Competition).filter(Competition.id == competition_id).first()
    if not db_comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # Mise à jour dynamique des champs fournis (non-null)
    update_data = comp_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_comp, key, value)
    
    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.delete("/{competition_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer une compétition")
def delete_competition(competition_id: int, db: Session = Depends(get_db)):
    """
    Supprime définitivement une compétition de la base de données.
    """
    db_comp = db.query(Competition).filter(Competition.id == competition_id).first()
    if not db_comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    
    db.delete(db_comp)
    db.commit()
    return None