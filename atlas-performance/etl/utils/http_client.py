# etl/utils/http_client.py
import time
import requests
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from requests.exceptions import RequestException

from etl.config import BASE_URL, HEADERS, REQUEST_DELAY, MAX_RETRIES, TIMEOUT
from etl.utils.logger import logger, log_warning, log_error, log_debug

# Base Cache Directory
CACHE_ROOT = Path("data/raw_json")

class APIClient:
    """
    Client HTTP singleton pour l'API-Football v3.
    Gère le rate limiting, les retries automatiques et le CACHE local.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APIClient, cls).__new__(cls)
            cls._instance.session = requests.Session()
            cls._instance.session.headers.update(HEADERS)
            cls._instance.last_request_time = 0
        return cls._instance

    def _wait_if_needed(self):
        """Force un délai entre les requêtes pour respecter le Rate Limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            sleep_time = REQUEST_DELAY - elapsed
            logger.debug(f"⏳ Rate limit: Pause de {sleep_time:.2f}s...")
            time.sleep(sleep_time)

    # --- MÉTHODES DE CACHE ---

    def _generate_filename(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """Génère un nom de fichier unique."""
        if not params:
            return f"{endpoint.replace('/', '_')}.json"
        
        sorted_params = sorted(params.items())
        param_str = "_".join([f"{k}-{v}" for k, v in sorted_params])
        safe_name = f"{endpoint.replace('/', '_')}_{param_str}"
        safe_name = re.sub(r'[^\w\-_\.]', '', safe_name)
        return f"{safe_name}.json"

    def _ensure_cache_dir(self, subdir: str = ""):
        """Crée le dossier de cache."""
        path = CACHE_ROOT
        if subdir:
            path = path / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_from_cache(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """Tente de récupérer la donnée depuis le cache JSON."""
        filename = self._generate_filename(endpoint, params)
        subdir = ""

        # Cas Spécial: StatistiqueMatches
        if endpoint == "fixtures/statistics":
            subdir = "StatistiqueMatches"
            if params and 'fixture' in params:
                 filename = f"{params['fixture']}.json"

        filepath = self._ensure_cache_dir(subdir) / filename
        
        if filepath.exists():
            log_debug(f"📦 CACHE HIT: {filename}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log_debug(f"⚠️ Cache read error: {e}")
                return None
        return None

    def save_to_cache(self, data: Any, endpoint: str, params: Dict[str, Any] = None):
        """Sauvegarde la réponse API en local."""
        filename = self._generate_filename(endpoint, params)
        subdir = ""

        if endpoint == "fixtures/statistics":
            subdir = "StatistiqueMatches"
            if params and 'fixture' in params:
                 filename = f"{params['fixture']}.json"

        path = self._ensure_cache_dir(subdir)
        filepath = path / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log_debug(f"💾 CACHE SAVED: {filename}")
        except Exception as e:
            log_debug(f"⚠️ Cache write error: {e}")

    # --- MÉTHODE PRINCIPALE ---

    def get(self, endpoint: str, params: dict = None, use_cache: bool = True):
        """
        Exécute une requête GET avec gestion Cache et Rate Limit.
        """
        # 1. Vérification Cache
        if use_cache:
            cached = self.get_from_cache(endpoint, params)
            if cached:
                return cached
        
        url = f"{BASE_URL}/{endpoint}"
        attempt = 0

        while attempt < MAX_RETRIES:
            self._wait_if_needed()
            
            try:
                logger.info(f"📡 GET {endpoint} | Params: {params}")
                response = self.session.get(url, params=params, timeout=TIMEOUT)
                self.last_request_time = time.time()

                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("errors"):
                        log_error(f"API Logic Error: {data['errors']}")
                        return None
                        
                    result = data.get("response", [])
                    
                    # 2. Sauvegarde Cache
                    if use_cache:
                        self.save_to_cache(result, endpoint, params)
                        
                    return result

                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 60 
                    log_warning(f"⛔ Rate Limit (429). Pause de {wait_time}s avant retry...")
                    time.sleep(wait_time)
                    attempt += 1
                    continue

                elif 500 <= response.status_code < 600:
                    wait_time = (attempt + 1) * 5
                    log_warning(f"Server Error ({response.status_code}). Retry dans {wait_time}s...")
                    time.sleep(wait_time)
                    attempt += 1
                    continue

                else:
                    log_error(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                    return None

            except RequestException as e:
                wait_time = (attempt + 1) * 5
                log_error(f"❌ Connection Error: {e}. Retry dans {wait_time}s...")
                time.sleep(wait_time)
                attempt += 1

        log_error(f"💀 Échec définitif après {MAX_RETRIES} tentatives pour {url}")
        return None

# Instance globale prête à l'emploi
api_client = APIClient()