
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

from etl.utils.http_client import api_client
from etl.utils.logger import log_info, log_error, log_success, log_warning
from app.database import SessionLocal
from app.models import Match, MatchStatistic

CACHE_DIR = Path("data/raw_json_StatistiqueMatches")

def ensure_cache_dir():
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        log_info(f"📁 Dossier cache créé: {CACHE_DIR}")

def fetch_and_cache_stats(match_id):
    """
    Récupère les stats d'un match.
    1. Vérifie le cache local.
    2. Si absent, appelle l'API.
    3. Sauvegarde en cache.
    """
    cache_file = CACHE_DIR / f"{match_id}.json"
    
    if cache_file.exists():
        # log_info(f"   📦 Cache trouvé pour match {match_id}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    # Fetch API
    log_info(f"   📡 API Call pour match {match_id}...")
    data = api_client.get("fixtures/statistics", params={"fixture": match_id})
    
    if data:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    return data

def load_stats_to_db(session, match_id, stats_data):
    if not stats_data:
        return 0, 0
        
    created = 0
    updated = 0
    
    # API format: [{"team": {id:..}, "statistics": [...]}, ...]
    for team_stat in stats_data:
        team_id = team_stat["team"]["id"]
        
        # Parse values
        raw = {item["type"]: item["value"] for item in team_stat["statistics"]}
        
        # Helper dict for values
        stat_values = {
            "shots_total": raw.get("Total Shots") or 0,
            "shots_on_goal": raw.get("Shots on Goal") or 0,
            "shots_off_goal": raw.get("Shots off Goal") or 0,
            "shots_blocked": raw.get("Blocked Shots") or 0,
            "shots_inside_box": raw.get("Shots insidebox") or 0,
            "shots_outside_box": raw.get("Shots outsidebox") or 0,
            "fouls": raw.get("Fouls") or 0,
            "corners": raw.get("Corner Kicks") or 0,
            "offsides": raw.get("Offsides") or 0,
            "ball_possession": str(raw.get("Ball Possession") or "0%"),
            "yellow_cards": raw.get("Yellow Cards") or 0,
            "red_cards": raw.get("Red Cards") or 0,
            "goalkeeper_saves": raw.get("Goalkeeper Saves") or 0,
            "passes_total": raw.get("Total passes") or 0,
            "passes_accurate": raw.get("Passes accurate") or 0
        }
        
        # Check existing
        existing = session.query(MatchStatistic).filter_by(match_id=match_id, team_id=team_id).first()
        
        if existing:
            # UPDATE
            for key, value in stat_values.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now() # FORCE UPDATE TIMESTAMP
            updated += 1
        else:
            # CREATE
            new_stat = MatchStatistic(
                match_id=match_id,
                team_id=team_id,
                **stat_values
            )
            session.add(new_stat)
            created += 1
            
    return created, updated

def main():
    log_info("🚀 === SCRIPT: FETCH MATCH STATISTICS (CACHE-FIRST) ===")
    ensure_cache_dir()
    
    session = SessionLocal()
    
    try:
        # 1. Sélectionner les matchs terminés
        matches = session.query(Match).filter(
            Match.status.in_(["FT", "AET", "PEN", "finished"])
        ).order_by(Match.date.desc()).all()
        
        log_info(f"🔎 {len(matches)} matchs terminés trouvés en base.")
        
        total_created = 0
        total_updated = 0
        
        for i, match in enumerate(matches, 1):
            # Fetch / Load
            try:
                stats_data = fetch_and_cache_stats(match.id)
                created, updated = load_stats_to_db(session, match.id, stats_data)
                total_created += created
                total_updated += updated
                
                if i % 10 == 0:
                    session.commit()
                    log_info(f"   ✅ Progression: {i}/{len(matches)} matchs traités.")
                    
            except Exception as e:
                log_error(f"Erreur match {match.id}: {e}")
                
        session.commit()
        log_success(f"🎉 Terminé! {total_created} statistiques chargées, {total_updated} mises à jour.")
        
    except Exception as e:
        log_error(f"Erreur script: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
