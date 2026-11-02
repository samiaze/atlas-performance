from typing import List
from fastapi import HTTPException

class PlayerNotFoundException(HTTPException):
    """Exception levée lorsqu'un joueur est introuvable."""
    def __init__(self, player_id: int):
        super().__init__(status_code=404, detail=f"Player with ID {player_id} not found")

class TeamNotFoundException(HTTPException):
    """Exception levée lorsqu'une équipe est introuvable."""
    def __init__(self, team_id: int):
        super().__init__(status_code=404, detail=f"Team with ID {team_id} not found")

class MatchNotFoundException(HTTPException):
    """Exception levée lorsqu'un match est introuvable."""
    def __init__(self, match_id: int):
        super().__init__(status_code=404, detail=f"Match with ID {match_id} not found")

class InvalidPerformanceDataException(HTTPException):
    """Exception levée lorsque les données de performance sont incohérentes."""
    def __init__(self, errors: List[str]):
        super().__init__(status_code=400, detail=f"Invalid performance data: {', '.join(errors)}")

class DuplicateResourceException(HTTPException):
    """Exception levée lors d'une tentative de création de doublon."""
    def __init__(self, resource: str):
        super().__init__(status_code=409, detail=f"{resource} already exists")