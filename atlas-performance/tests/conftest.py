import pytest
import os
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Competition, Team, Player, Match, Performance

# Utilisation d'un fichier SQLite pour les tests (plus stable que :memory: pour les threads)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Crée les tables au début de la session de test et les supprime à la fin."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Nettoyage du fichier
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def db_session():
    """Crée une nouvelle session pour chaque test (rollback automatique)."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Client API simulé avec injection de la DB de test."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

# --- FIXTURES DE DONNÉES (Données pré-remplies) ---

@pytest.fixture
def sample_competition(db_session):
    comp = Competition(id=1, name="Test League", season=2024, country="TestLand")
    db_session.add(comp)
    db_session.commit()
    return comp

@pytest.fixture
def sample_team_home(db_session, sample_competition):
    team = Team(id=10, name="Home FC", country="TestLand", competition_api_id=sample_competition.id)
    db_session.add(team)
    db_session.commit()
    return team

@pytest.fixture
def sample_team_away(db_session, sample_competition):
    team = Team(id=20, name="Away United", country="TestLand", competition_api_id=sample_competition.id)
    db_session.add(team)
    db_session.commit()
    return team

@pytest.fixture
def sample_player(db_session, sample_team_home):
    player = Player(
        id=100, 
        name="Star Player", 
        position="Forward", 
        team_id=sample_team_home.id,
        nationality="TestLand"
    )
    db_session.add(player)
    db_session.commit()
    return player

@pytest.fixture
def sample_match(db_session, sample_competition, sample_team_home, sample_team_away):
    match = Match(
        id=500,
        date=datetime.now(),
        status="FT",
        home_team_id=sample_team_home.id,
        away_team_id=sample_team_away.id,
        home_score=2,
        away_score=1,
        competition_id=sample_competition.id
    )
    db_session.add(match)
    db_session.commit()
    return match

@pytest.fixture
def sample_performance(db_session, sample_match, sample_player):
    perf = Performance(
        id=900,
        match_id=sample_match.id,
        player_id=sample_player.id,
        rating=8.5,
        goals=1,
        minutes_played=90
    )
    db_session.add(perf)
    db_session.commit()
    return perf