from app.database import SessionLocal, engine
from sqlalchemy import text

def clean_database():
    session = SessionLocal()
    try:
        # On désactive les contraintes de clé étrangère temporairement pour tout supprimer
        session.execute(text("TRUNCATE TABLE performances, players, matches, teams, competitions RESTART IDENTITY CASCADE;"))
        session.commit()
        print("✅ Base de données vidée avec succès !")
    except Exception as e:
        session.rollback()
        print(f"❌ Erreur : {e}")
    finally:
        session.close()

if __name__ == "__main__":
    clean_database()