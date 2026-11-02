import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

class APIFootballClient:
    def __init__(self):
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': os.getenv("RAPIDAPI_HOST"),
            'x-rapidapi-key': os.getenv("RAPIDAPI_KEY")
        }
        self.logger = logging.getLogger(__name__)

    def _get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errors"):
                self.logger.error(f"API Error: {data['errors']}")
                return None
                
            return data.get("response")
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None

    def get_league(self, league_id, season):
        return self._get("leagues", {"id": league_id, "season": season})

    def get_teams(self, league_id, season):
        return self._get("teams", {"league": league_id, "season": season})

    def get_fixture_details(self, fixture_id):
        # Récupère les détails d'un match (y compris stats joueurs)
        return self._get("fixtures", {"id": fixture_id})
    
    def get_fixture_players(self, fixture_id):
        # Récupère spécifiquement les stats des joueurs pour ce match
        return self._get("fixtures/players", {"fixture": fixture_id})