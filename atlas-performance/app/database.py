# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Construction de l'URL de connexion PostgreSQL
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "atlasperformance")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Création du moteur (Engine)
# pool_size=10 : Nombre de connexions maintenues ouvertes
# max_overflow=20 : Connexions supplémentaires autorisées lors des pics de charge
engine = create_engine(
    DATABASE_URL, 
    pool_size=10, 
    max_overflow=20,
    echo=False # Mettre à True pour voir les requêtes SQL brutes
)

# Fabrique de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe de base pour tous les modèles
class Base(DeclarativeBase):
    pass

# Dépendance pour FastAPI
def get_db():
    """Crée une session DB pour une requête et la ferme ensuite."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()