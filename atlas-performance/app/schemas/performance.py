from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

class PerformanceBase(BaseModel):
    match_id: int
    player_id: int
    rating: Optional[float] = None
    minutes_played: int = 0
    goals: int = 0
    assists: int = 0
    shots_total: int = 0
    shots_on_target: int = 0
    passes_total: int = 0
    passes_accurate: int = 0
    tackles: int = 0
    interceptions: int = 0
    fouls_committed: int = 0
    fouls_drawn: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    saves: int = 0

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Rating must be between 0 and 10')
        return v

    @field_validator('minutes_played')
    @classmethod
    def validate_minutes(cls, v):
        if v < 0 or v > 150: # Prolongations incluses
            raise ValueError('Minutes played invalid')
        return v
    
    # On pourrait ajouter un validateur générique pour tous les int >= 0
    
class PerformanceCreate(PerformanceBase):
    pass

class PerformanceUpdate(BaseModel):
    rating: Optional[float] = None
    goals: Optional[int] = None
    # ...

class PerformanceResponse(PerformanceBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)