from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.team import TeamResponse
from app.schemas.performance import PerformanceResponse

class MatchBase(BaseModel):
    date: datetime
    round: Optional[str] = None
    status: Optional[str] = None
    venue: Optional[str] = None
    referee: Optional[str] = None
    home_team_id: int
    away_team_id: int
    home_score: Optional[int] = 0
    away_score: Optional[int] = 0
    competition_id: int

class MatchCreate(MatchBase):
    id: int

class MatchUpdate(BaseModel):
    status: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None

class MatchResponse(MatchBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MatchWithDetails(MatchResponse):
    """Match avec les objets Equipes complets et les stats."""
    home_team: Optional[TeamResponse] = None
    away_team: Optional[TeamResponse] = None
    # Pour éviter de surcharger, on peut mettre les perfs en optionnel ou sur une autre route
    performances: List[PerformanceResponse] = []