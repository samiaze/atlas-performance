# etl/run_etl.py
import time
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# --- IMPORTS MODULES ETL ---
from etl.config import LOG_DIR
from etl.utils.logger import logger, log_info, log_error, log_success
from etl.extract import competitions as ext_comp
from etl.extract import teams as ext_teams
from etl.extract import matches as ext_matches
from etl.extract import players as ext_players
from etl.transform import cleaners, validators
from etl.load import loaders

# Fichier d'état pour le mode incrémental
STATE_FILE = LOG_DIR / "etl_state.json"

def get_last_run_date():
    """Récupère la date de dernière exécution réussie."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data.get('last_run'))
    return None

def update_last_run_date():
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({'last_run': datetime.now().isoformat()}, f)
    except Exception: pass

def run_full_etl():
    """
    Exécute le pipeline ETL complet.
    Récupère TOUT, nettoie TOUT, charge TOUT.
    """
    start_time = time.time()
    log_info("🚀 === DÉMARRAGE DU PIPELINE ETL (MODE: FULL) ===")

    try:
        # ---------------------------------------------------------
        # PHASE 1 : EXTRACTION
        # ---------------------------------------------------------
        log_info("📡 --- EXTRACTION ---")
        
        # 1. Compétitions
        competitions_list = ext_comp.fetch_all_competitions()
        if not competitions_list:
            log_error("⛔ Aucune compétition trouvée.")
            sys.exit(1)

        # Init Containers Globaux
        global_matches = []
        global_performances = []
        global_teams = []
        global_players_dict = {}

        # 2. Boucle par Compétition (Ordre Strict)
        for comp in competitions_list:
            league_id = comp['api_id']
            season = comp['season']
            name = comp['name']
            
            log_info(f"🏆 Traitement Compétition : {name} (ID: {league_id}, Saison: {season})")

            # A. Matchs (Cache-First)
            comp_matches = ext_matches.fetch_all_matches([comp])
            global_matches.extend(comp_matches)
            
            # B. Performances (Source de Vérité)
            # Pour la stratégie économique/cache, on prend tous les matchs terminés
            comp_perfs = ext_players.fetch_all_performances(comp_matches)
            global_performances.extend(comp_perfs)
            
            # C. Identification des actifs (Ceux qui ont joué)
            active_p_ids = {p['player_api_id'] for p in comp_perfs}
            active_t_ids = {p['team_api_id'] for p in comp_perfs if p.get('team_api_id')}
            
            log_info(f"   🎯 Cible {name} : {len(active_p_ids)} joueurs et {len(active_t_ids)} équipes actifs.")

            # D. Équipes (Filtrage)
            # On récupère toutes les équipes de la ligue (1 requête) puis on filtre
            league_teams = ext_teams.fetch_all_teams([comp])
            active_teams = [t for t in league_teams if t['api_id'] in active_t_ids]
            global_teams.extend(active_teams)

            # E. Joueurs (Mode Hybride)
            # On ne cherche que les joueurs des équipes actives + fallback individuel pour les actifs manquants
            comp_players = ext_players.fetch_players_hybrid(active_teams, season, active_p_ids, league_id)
            
            # Ajout au dictionnaire global (Upsert pour éviter doublons si joueur change de club/comp)
            for p in comp_players:
                # On privilégie la version la plus récente (écrasement)
                global_players_dict[p['api_id']] = p

        # Conversion du dict joueurs en liste
        global_players = list(global_players_dict.values())

        log_info(f"📊 BILAN GLOBAL EXTRACTION : "
                 f"{len(competitions_list)} Comps, "
                 f"{len(global_matches)} Matchs, "
                 f"{len(global_performances)} Perfs, "
                 f"{len(global_players)} Joueurs uniques.")


        # ---------------------------------------------------------
        # PHASE 2 : TRANSFORMATION
        # ---------------------------------------------------------
        log_info("🧹 --- TRANSFORMATION ---")
        cl_competitions = [cleaners.clean_competition_data(c) for c in competitions_list]
        cl_teams = [cleaners.clean_team_data(t) for t in global_teams]
        cl_matches = [cleaners.clean_match_data(m) for m in global_matches]
        cl_players = [cleaners.clean_player_data(p) for p in global_players]
        cl_perfs = [cleaners.clean_performance_data(p) for p in global_performances]

        # Validation
        val_matches, val_players, val_perfs = validators.validate_all_data(
            cl_matches, cl_players, cl_perfs
        )

        # ---------------------------------------------------------
        # PHASE 3 : CHARGEMENT
        # ---------------------------------------------------------
        log_info("💾 --- CHARGEMENT ---")
        
        loaders.load_all_data(
            cleaned_competitions=cl_competitions,
            cleaned_teams=cl_teams,
            cleaned_matches=val_matches,
            cleaned_players=val_players,
            cleaned_perfs=val_perfs
        )
        
        update_last_run_date()

    except Exception as e:
        log_error(f"❌ ERREUR CRITIQUE DU PIPELINE : {e}")
        sys.exit(1)
    
    duration = time.time() - start_time
    log_success(f"✅ TERMINE en {duration:.2f} s")


def run_incremental_etl():
    """
    Mode Incrémental : Ne traite que les matchs récents.
    """
    last_run = get_last_run_date()
    if not last_run:
        log_warning("⚠️ Pas d'exécution précédente trouvée. Bascule en mode FULL.")
        return run_full_etl()

    log_info(f"🚀 === DÉMARRAGE ETL INCRÉMENTAL (Depuis {last_run}) ===")
    
    log_warning("ℹ️ Mode incrémental complet non implémenté dans cette version v1.")
    log_warning("ℹ️ Exécution du mode FULL par sécurité.")
    run_full_etl()

def main():
    parser = argparse.ArgumentParser(description="AtlasPerformance ETL Pipeline")
    parser.add_argument('--mode', choices=['full', 'incremental'], default='full', help="Mode d'exécution")
    parser.add_argument('-v', '--verbose', action='store_true', help="Afficher les logs de debug")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(10) # DEBUG

    if args.mode == 'full':
        run_full_etl()
    else:
        run_incremental_etl()

if __name__ == "__main__":
    main()