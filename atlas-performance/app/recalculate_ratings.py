from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Performance
from app.database import DATABASE_URL
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

def calculate_custom_rating(perf):
    """Calculates rating based on Performance object attributes."""
    
    # 1. Base Rating
    rating = 6.0
    
    # 2. Bonuses
    rating += float(perf.goals or 0) * 1.0
    rating += float(perf.assists or 0) * 0.8
    rating += float(perf.shots_on_target or 0) * 0.2
    rating += float(perf.saves or 0) * 0.5
    rating += float(perf.interceptions or 0) * 0.1
    rating += float(perf.tackles or 0) * 0.1
    rating += float(perf.dribbles_success or 0) * 0.1
    rating += float(perf.fouls_drawn or 0) * 0.1
    
    # Passes Logic
    passes_total = perf.passes_total or 0
    passes_accurate = perf.passes_accurate or 0
    
    if passes_total > 5:
        pass_rate = passes_accurate / passes_total
        if pass_rate > 0.85:
            rating += 0.3
        elif pass_rate < 0.70:
            rating -= 0.3

    # 3. Penalties
    rating -= float(perf.yellow_cards or 0) * 1.0
    rating -= float(perf.red_cards or 0) * 3.0
    rating -= float(perf.fouls_committed or 0) * 0.2
    
    # Shots off target
    shots_total = perf.shots_total or 0
    shots_on = perf.shots_on_target or 0
    shots_off = shots_total - shots_on
    if shots_off > 0:
        rating -= shots_off * 0.1

    # 4. Constraints
    minutes = perf.minutes_played or 0
    if minutes < 15:
        return None
    
    return max(1.0, min(10.0, round(rating, 1)))

def main():
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        performances = db.query(Performance).all()
        print(f"Found {len(performances)} performances to recalculate.")
        
        updated_count = 0
        for p in performances:
            new_rating = calculate_custom_rating(p)
            
            # Update only if changed (optional check, but good for logging)
            if p.rating != new_rating:
                p.rating = new_rating
                updated_count += 1
        
        db.commit()
        print(f"Successfully updated {updated_count} ratings.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
