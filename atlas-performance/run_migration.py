import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, Base
from app.models import MatchStatistic

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
