from sqlalchemy import text
from app.database import SessionLocal
from etl.utils.logger import log_info, log_success, log_error

def check_database_content():
    session = SessionLocal()
    try:
        print("\n🔎 --- AUDIT DE LA BASE DE DONNÉES ---")
        
        # 1. Compter les lignes
        tables = ['competitions', 'teams', 'matches', 'players', 'performances']
        for table in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"📌 Table {table.upper().ljust(15)} : {count} enregistrements")

        # 2. Vérifier un match précis (Exemple)
        print("\n⚽ --- EXEMPLE DE MATCH ---")
        match = session.execute(text("""
            SELECT m.date, t1.name as home, t2.name as away, m.home_score, m.away_score, m.status
            FROM matches m
            JOIN teams t1 ON m.home_team_id = t1.id
            JOIN teams t2 ON m.away_team_id = t2.id
            LIMIT 1
        """)).first()
        
        if match:
            print(f"Match : {match.home} vs {match.away}")
            print(f"Score : {match.home_score} - {match.away_score} ({match.status})")
            print(f"Date  : {match.date}")
        else:
            print("⚠️ Aucun match trouvé.")

        # 3. Vérifier une stat joueur
        print("\n🏃 --- TOP PERFORMANCE (Exemple) ---")
        perf = session.execute(text("""
            SELECT p.name, t.name as team, pf.rating, pf.minutes_played
            FROM performances pf
            JOIN players p ON pf.player_id = p.id
            JOIN teams t ON p.team_id = t.id
            WHERE pf.rating IS NOT NULL
            ORDER BY pf.rating DESC
            LIMIT 1
        """)).first()

        if perf:
            print(f"Joueur : {perf.name} ({perf.team})")
            print(f"Note   : {perf.rating}/10 en {perf.minutes_played} min")
        else:
            print("⚠️ Aucune performance trouvée.")

        print("\n✅ AUDIT TERMINÉ.")

    except Exception as e:
        log_error(f"Erreur audit : {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_database_content()