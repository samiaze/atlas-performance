from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.player import PlayerResponse

class TeamBase(BaseModel):
    name: str
    code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = None
    founded: Optional[int] = None
    logo: Optional[str] = None
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    competition_api_id: Optional[int] = None

class TeamCreate(TeamBase):
    id: int

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    venue_name: Optional[str] = None

class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TeamWithPlayers(TeamResponse):
    """Équipe avec la liste complète des joueurs."""
    players: List[PlayerResponse] = []