# etl/utils/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from etl.config import LOG_FILE, LOG_DIR

def setup_logger(name="AtlasETL"):
    """Configure et retourne un logger robuste."""
    
    # Créer le dossier logs s'il n'existe pas
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # On capture tout

    # Vérifier si des handlers existent déjà pour éviter les doublons
    if logger.hasHandlers():
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. File Handler (Fichier avec rotation 5MB)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 2. Console Handler (Sortie Standard)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Moins verbeux dans la console
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Instance globale
logger = setup_logger()

# Fonctions helper pour simplifier l'utilisation
def log_info(msg): logger.info(msg)
def log_success(msg): logger.info(f"✅ {msg}")
def log_warning(msg): logger.warning(f"⚠️ {msg}")
def log_error(msg): logger.error(f"❌ {msg}")
def log_debug(msg): logger.debug(msg)