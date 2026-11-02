from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CompetitionBase(BaseModel):
    """Champs partagés pour la Compétition."""
    name: str = Field(..., min_length=3, max_length=100, description="Nom officiel de la compétition")
    season: int = Field(..., ge=2020, le=2030, description="Année de la saison")
    country: Optional[str] = Field(None, description="Pays organisateur")
    logo: Optional[str] = Field(None, description="URL du logo")
    flag: Optional[str] = Field(None, description="URL du drapeau du pays")

class CompetitionCreate(CompetitionBase):
    """Schéma pour la création (champs obligatoires)."""
    # On pourrait ajouter 'id' ici si on veut forcer l'ID manuel (ce que tu fais dans l'ETL)
    id: int = Field(..., description="ID unique API-Football")

class CompetitionUpdate(BaseModel):
    """Schéma pour la mise à jour (tout est optionnel)."""
    name: Optional[str] = None
    season: Optional[int] = None
    country: Optional[str] = None
    logo: Optional[str] = None
    flag: Optional[str] = None

class CompetitionResponse(CompetitionBase):
    """Schéma complet pour la réponse API."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)