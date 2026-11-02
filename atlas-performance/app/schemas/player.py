from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

class PlayerBase(BaseModel):
    name: str = Field(..., min_length=1)
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    age: Optional[int] = Field(None, ge=15, le=50)
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    height: Optional[int] = Field(None, description="Taille en cm")
    weight: Optional[int] = Field(None, description="Poids en kg")
    photo: Optional[str] = None
    position: Optional[str] = None
    number: Optional[int] = None
    team_id: int

class PlayerCreate(PlayerBase):
    id: int # ID manuel API-Football

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    number: Optional[int] = None
    team_id: Optional[int] = None
    # ... autres champs si besoin

class PlayerResponse(PlayerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PlayerWithStats(PlayerResponse):
    """Joueur enrichi avec des agrégats calculés."""
    total_matches: int = 0
    total_goals: int = 0
    total_assists: int = 0
    average_rating: Optional[float] = 0.0