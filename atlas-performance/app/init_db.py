import logging
from app.database import engine, Base
# Import impératif des modèles pour que SQLAlchemy les détecte
from app.models import Competition, Team, Match, Player, Performance

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Crée toutes les tables définies dans les modèles."""
    try:
        logger.info("Création des tables dans la base de données...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès !")
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables : {e}")

if __name__ == "__main__":
    init_db()