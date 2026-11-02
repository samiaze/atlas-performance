# etl/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --- API CREDENTIALS ---
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "v3.football.api-sports.io")

if not RAPIDAPI_KEY:
    raise ValueError("❌ ERREUR: La clé RAPIDAPI_KEY est manquante dans le fichier .env")

# --- API CONSTANTS ---
BASE_URL = f"https://{RAPIDAPI_HOST}"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST
}

# --- RATE LIMITING ---
# Plan Gratuit : 100 req/jour. Délai de sécurité augmenté pour gérer le volume.
REQUEST_DELAY = 6.1 
MAX_RETRIES = 3
TIMEOUT = 10 

# --- PATHS ---
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "etl.log"

# --- COMPETITIONS CONFIGURATION ---
COMPETITIONS = {
    "WORLD_CUP_22": {
        "id": 1,          # Coupe du Monde
        "season": 2022,   
        "code": "WC"
    },
    "CAN_23": {
        "id": 6,          # Coupe d'Afrique des Nations
        "season": 2023,   # Saison API (même si jouée en 2024)
        "code": "CAN"
    }
}