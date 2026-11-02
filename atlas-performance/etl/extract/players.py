from typing import List, Dict, Any, Set, Optional
from etl.utils.http_client import api_client
from etl.utils.logger import log_info, log_error, log_success

def get_correct_stat(statistics: List[Dict], target_team_id: int = None, target_league_id: int = None) -> Optional[Dict]:
    """
    Cherche la statistique correspondante (Priorité ID > Nom).
    Strictement optimisé pour CAN et World Cup.
    """
    if not statistics: return None

    # 1. Priorité ABSOLUE : Match l'ID de l'équipe
    if target_team_id:
        for stat in statistics:
            if stat['team']['id'] == target_team_id:
                return stat

    # 2. Priorité HAUTE : Match l'ID exact de la ligue
    if target_league_id:
        for stat in statistics:
            if stat['league']['id'] == target_league_id:
                return stat

    # 3. Fallback : Mots-clés spécifiques CAN et CDM uniquement
    if target_league_id: 
        # On a retiré "Euro" et "Copa America"
        keywords = ["World Cup", "Africa Cup", "CAN", "Nations Cup"]
        
        for stat in statistics:
            league_name = stat['league'].get('name', '')
            for kw in keywords:
                if kw in league_name:
                    return stat

    # 4. Dernier recours
    return statistics[0]

# --- 1. RÉCUPÉRATION INDIVIDUELLE ---

def fetch_player_details_by_id(player_id: int, season: int, target_league_id: int = None) -> Dict[str, Any]:
    """Récupère un joueur unique."""
    data = api_client.get("players", params={"id": player_id, "season": season})
    if not data: return None

    try:
        item = data[0]
        p = item['player']
        
        # Utilisation de la version corrigée
        stats = get_correct_stat(item['statistics'], target_league_id=target_league_id)
        
        if not stats: return None 

        birth_date = None
        if p.get('birth') and p['birth'].get('date'):
            birth_date = p['birth']['date']

        return {
            "api_id": p['id'],
            "name": p['name'],
            "firstname": p['firstname'],
            "lastname": p['lastname'],
            "age": p['age'],
            "birth_date": birth_date,
            "nationality": p['nationality'],
            "height": p['height'],
            "weight": p['weight'],
            "photo": p['photo'],
            "position": stats['games']['position'],
            "number": stats['games']['number'],
            "team_api_id": stats['team']['id']
        }
    except Exception as e:
        return None

# --- 2. SQUADS PAR ÉQUIPE ---

def fetch_players_by_team(team_id: int, season: int) -> List[Dict[str, Any]]:
    """
    Récupère la liste des joueurs (squad) d'une équipe.
    MODE ÉCO : Limité à 1 page (20 joueurs) pour économiser le quota.
    """
    log_info(f"Extraction joueurs pour Équipe {team_id}...")
    
    all_players = []
    page = 1
    
    while True:
        # LIMITATION API FREE PLAN : Max 3 pages
        if page > 3:
            break

        data = api_client.get("players", params={"team": team_id, "season": season, "page": page})
        if not data: break
            
        for item in data:
            try:
                p = item['player']
                stats = item['statistics'][0] # On prend les stats générales pour la position
                
                # Parsing date de naissance (YYYY-MM-DD)
                birth_date = None
                if p.get('birth') and p['birth'].get('date'): birth_date = p['birth']['date']

                all_players.append({
                    "api_id": p['id'],
                    "name": p['name'],
                    "firstname": p['firstname'],
                    "lastname": p['lastname'],
                    "age": p['age'],
                    "birth_date": birth_date,
                    "nationality": p['nationality'],
                    "height": p['height'],
                    "weight": p['weight'],
                    "photo": p['photo'],
                    "position": stats['games']['position'],
                    "number": stats['games']['number'],
                    "team_api_id": team_id 
                })
            except: continue
        
        # Si on a moins de 20 résultats, c'est la dernière page
        if len(data) < 20:
            break
        page += 1
    return all_players


def fetch_players_hybrid(teams: List[Dict[str, Any]], season: int, active_player_ids: Set[int], league_id: int) -> List[Dict[str, Any]]:
    """
    Stratégie Hybride Corrigée.
    """
    fetched_players = {}
    
    # 1. Squads (Masse)
    log_info(f"🔄 ÉTAPE 1 : Extraction par Équipe ({len(teams)} équipes)...")
    for i, team in enumerate(teams, 1):
        squad = fetch_players_by_team(team['api_id'], season)
        for player in squad:
            if player['api_id'] in active_player_ids:
                fetched_players[player['api_id']] = player
        
        if i % 10 == 0: log_info(f"   Équipes : {i}/{len(teams)}")

    # 2. Individuel (Manquants)
    found_ids = set(fetched_players.keys())
    missing_ids = active_player_ids - found_ids
    
    if missing_ids:
        log_info(f"🔄 ÉTAPE 2 : Récupération individuelle ({len(missing_ids)} manquants)...")
        count = 0
        for pid in missing_ids:
            # On passe league_id pour le fallback intelligent
            p_data = fetch_player_details_by_id(pid, season, target_league_id=league_id)
            if p_data:
                fetched_players[pid] = p_data
            
            count += 1
            if count % 10 == 0: log_info(f"   Individuels : {count}/{len(missing_ids)}")

    return list(fetched_players.values())


# --- 3. PERFORMANCES ---

def fetch_player_statistics(fixture_id: int) -> List[Dict[str, Any]]:
    """
    Récupère les stats détaillées de TOUS les joueurs pour UN match.
    Endpoint: /fixtures/players
    """
    data = api_client.get("fixtures/players", params={"fixture": fixture_id})
    if not data: return []
    performances = []
    
    # Structure data: Une liste de 2 éléments (un par équipe)
    for team_data in data:
        for p_entry in team_data['players']:
            try:
                p_id = p_entry['player']['id']
                raw_stats = p_entry['statistics'][0] # Stats du match
                
                # --- LOGIQUE DE NETTOYAGE ---
                
                # Extraction des passes (nécessaire avant le calcul de la note)
                passes_total = raw_stats['passes']['total'] or 0
                # Note: 'accuracy' est souvent une chaine représentant un nombre ou un pourcentage. 
                # Dans le contexte observé, il semble agir comme un compteur (ou le code legacy le traite comme tel).
                # On tente de le convertir proprement.
                try: 
                    passes_accurate_raw = raw_stats['passes']['accuracy']
                    if passes_accurate_raw is None:
                        passes_accurate = 0
                    else:
                        passes_accurate = int(str(passes_accurate_raw).replace('%', ''))
                except:
                    passes_accurate = 0

                # 1. Calcul de la Note Personnalisée (Atlas Algorithm)
                # Base 6.0
                custom_rating = 6.0
                
                # Bonus
                custom_rating += (raw_stats['goals']['total'] or 0) * 1.0
                custom_rating += (raw_stats['goals']['assists'] or 0) * 0.8
                custom_rating += (raw_stats['shots']['on'] or 0) * 0.2
                custom_rating += (raw_stats['goals']['saves'] or 0) * 0.5
                custom_rating += (raw_stats['tackles']['interceptions'] or 0) * 0.1
                custom_rating += (raw_stats['tackles']['total'] or 0) * 0.1
                custom_rating += (raw_stats['dribbles']['success'] or 0) * 0.1
                custom_rating += (raw_stats['fouls']['drawn'] or 0) * 0.1
                
                # Passes Logic
                if passes_total > 5:
                    pass_rate = passes_accurate / passes_total if passes_total > 0 else 0
                    if pass_rate > 0.85:
                        custom_rating += 0.3
                    elif pass_rate < 0.70:
                        custom_rating -= 0.3

                # Malus
                custom_rating -= (raw_stats['cards']['yellow'] or 0) * 1.0
                custom_rating -= (raw_stats['cards']['red'] or 0) * 3.0
                custom_rating -= (raw_stats['fouls']['committed'] or 0) * 0.2
                
                # Tirs non cadrés (Total - Cadrés)
                shots_off = (raw_stats['shots']['total'] or 0) - (raw_stats['shots']['on'] or 0)
                if shots_off > 0:
                    custom_rating -= shots_off * 0.1

                # Contraintes
                minutes = raw_stats['games']['minutes'] or 0
                if minutes < 15:
                    final_rating = None # Pas de note si < 15 min
                else:
                    # Clamp entre 1 et 10
                    final_rating = max(1.0, min(10.0, round(custom_rating, 1)))

                # Construction de l'objet Performance
                performances.append({
                    "player_api_id": p_id,
                    "match_api_id": fixture_id,
                    "team_api_id": team_data['team']['id'],
                    "rating": final_rating,
                    "minutes_played": raw_stats['games']['minutes'] or 0,
                    "goals": raw_stats['goals']['total'] or 0,
                    "assists": raw_stats['goals']['assists'] or 0,
                    "shots_total": raw_stats['shots']['total'] or 0,
                    "shots_on_target": raw_stats['shots']['on'] or 0,
                    "passes_total": passes_total,
                    "passes_accurate": passes_accurate,
                    "tackles": raw_stats['tackles']['total'] or 0,
                    "interceptions": raw_stats['tackles']['interceptions'] or 0,
                    "fouls_committed": raw_stats['fouls']['committed'] or 0,
                    "fouls_drawn": raw_stats['fouls']['drawn'] or 0,
                    "yellow_cards": raw_stats['cards']['yellow'] or 0,
                    "red_cards": raw_stats['cards']['red'] or 0,
                    "saves": raw_stats['goals']['saves'] or 0
                })
            except Exception as e:
                log_error(f"Erreur parsing perf joueur {p_entry.get('player', {}).get('id')}: {e}")
                continue
    return performances

def fetch_all_performances(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Itère sur les matchs demandés pour récupérer les stats."""
    all_perfs = []
    count = 0
    
    # On filtre uniquement les matchs terminés
    finished_matches = [m for m in matches if m['status'] in ['FT', 'AET', 'PEN']]
    
    log_info(f"Début extraction performances pour {len(finished_matches)} matchs ciblés...")

    for match in finished_matches:
        perfs = fetch_player_statistics(match['api_id'])
        all_perfs.extend(perfs)
        count += 1
        
        # Log moins fréquent
        if count % 2 == 0:
            log_info(f"Progression stats: {count}/{len(finished_matches)} matchs traités.")

    log_success(f"Total performances extraites: {len(all_perfs)}")
    return all_perfs