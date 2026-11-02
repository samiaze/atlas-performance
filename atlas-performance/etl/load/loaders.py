# etl/load/loaders.py
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models import Competition, Team, Match, Player, Performance
from etl.utils.logger import log_info, log_error, log_success, log_warning

def load_competitions(session: Session, competitions_data: List[Dict[str, Any]]) -> Dict[int, int]:
    """
    Charge les compétitions et retourne un mapping {api_id: db_id}.
    Logique: Upsert basé sur (name, season).
    """
    mapping = {}
    count_created = 0
    count_updated = 0

    for comp_data in competitions_data:
        api_id = comp_data.pop('api_id') # On enlève l'ID API pour ne pas confondre
        
        try:
            # Vérifier si existe déjà (Unicité Nom + Saison)
            existing = session.query(Competition).filter_by(
                name=comp_data['name'], 
                season=comp_data['season']
            ).first()

            if existing:
                # UPDATE
                for key, value in comp_data.items():
                    setattr(existing, key, value)
                session.flush()
                mapping[api_id] = existing.id
                count_updated += 1
            else:
                # INSERT
                # Note: On force l'ID de l'API comme ID DB pour simplifier, 
                # ou on laisse l'auto-incrément. Ici on utilise l'API ID si possible.
                new_comp = Competition(id=api_id, **comp_data)
                session.add(new_comp)
                session.flush() # Récupère l'ID généré si auto-incrément
                mapping[api_id] = new_comp.id
                count_created += 1

        except Exception as e:
            log_error(f"Erreur chargement compétition {comp_data.get('name')}: {e}")
            continue
    return mapping

def load_teams(session: Session, teams_data: List[Dict[str, Any]], comp_mapping: Dict[int, int]) -> Dict[int, int]:
    """
    Charge les équipes.
    Logique: Upsert basé sur l'ID (API ID == DB ID pour les équipes).
    """
    mapping = {}
    count = 0

    # DEDUPLICATION: On ne garde qu'une entrée par équipe (la dernière vue ou la première)
    # Les équipes peuvent apparaitre dans plusieurs compétitions
    unique_teams = {}
    for t in teams_data:
        unique_teams[t['api_id']] = t
    
    deduplicated_teams = list(unique_teams.values())

    for team_data in deduplicated_teams:
        api_id = team_data.pop('api_id')
        comp_api_id = team_data.pop('competition_api_id') # Non utilisé dans le modèle Team actuel mais présent dans data
        
        # Résolution FK
        if comp_api_id not in comp_mapping:
            log_warning(f"Équipe {team_data['name']} ignorée: Compétition {comp_api_id} inconnue.")
            continue
            
        # On ne stocke pas competition_id dans Team selon le modèle 1.2, 
        # mais si le modèle évolue, on l'a.
        # Le modèle 1.2 ne lie pas Team à Competition directement (relation via Match), 
        # donc on ignore comp_api_id pour l'insertion.

        try:
            # Upsert via merge (car ID est PK)
            team = Team(id=api_id, **team_data)
            session.merge(team)
            mapping[api_id] = api_id # DB ID est le même que API ID
            count += 1
        except Exception as e:
            log_error(f"Erreur chargement équipe {team_data.get('name')}: {e}")

    log_success(f"Équipes traitées: {count}")
    return mapping

def load_matches(
    session: Session, 
    matches_data: List[Dict[str, Any]], 
    team_mapping: Dict[int, int], 
    comp_mapping: Dict[int, int]
) -> Dict[int, int]:
    """
    Charge les matchs.
    Logique: Upsert via merge sur ID.
    """
    mapping = {}
    count = 0

    for match_data in matches_data:
        api_id = match_data.pop('api_id')
        home_api = match_data.pop('home_team_api_id')
        away_api = match_data.pop('away_team_api_id')
        comp_api = match_data.pop('competition_api_id')

        # Vérification des FKs
        if home_api not in team_mapping or away_api not in team_mapping:
            log_warning(f"Match {api_id} ignoré: Équipe introuvable.")
            continue
        if comp_api not in comp_mapping:
            log_warning(f"Match {api_id} ignoré: Compétition introuvable.")
            continue

        try:
            match = Match(
                id=api_id,
                home_team_id=team_mapping[home_api],
                away_team_id=team_mapping[away_api],
                competition_id=comp_mapping[comp_api],
                **match_data
            )
            session.merge(match)
            mapping[api_id] = api_id
            count += 1
        except Exception as e:
            log_error(f"Erreur chargement match {api_id}: {e}")

    log_success(f"Matchs traités: {count}")
    return mapping

def load_players(session: Session, players_data: List[Dict[str, Any]], team_mapping: Dict[int, int]) -> Dict[int, int]:
    """
    Charge les joueurs.
    Logique: Upsert via merge sur ID.
    """
    mapping = {}
    count = 0

    for p_data in players_data:
        api_id = p_data.pop('api_id')
        team_api = p_data.pop('team_api_id')

        if team_api not in team_mapping:
            # Peut arriver lors de transferts ou sélections nationales non chargées
            continue

        try:
            player = Player(
                id=api_id,
                team_id=team_mapping[team_api],
                **p_data
            )
            session.merge(player)
            mapping[api_id] = api_id
            count += 1
        except Exception as e:
            log_error(f"Erreur chargement joueur {p_data.get('name')}: {e}")

    log_success(f"Joueurs traités: {count}")
    return mapping

def load_performances(
    session: Session, 
    perfs_data: List[Dict[str, Any]], 
    player_map: Dict[int, int], 
    match_map: Dict[int, int]
) -> int:
    """
    Charge les performances.
    Logique: Recherche (match_id, player_id). Si existe Update, sinon Insert.
    """
    count = 0
    updated = 0

    for perf_data in perfs_data:
        p_api = perf_data.pop('player_api_id')
        m_api = perf_data.pop('match_api_id')

        # Vérification FK
        if p_api not in player_map or m_api not in match_map:
            continue
        
        db_p_id = player_map[p_api]
        db_m_id = match_map[m_api]

        try:
            # Vérifier unicité
            existing = session.query(Performance).filter_by(
                match_id=db_m_id, 
                player_id=db_p_id
            ).first()

            if existing:
                # Update
                for k, v in perf_data.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                # Insert
                new_perf = Performance(
                    match_id=db_m_id,
                    player_id=db_p_id,
                    **perf_data
                )
                session.add(new_perf)
                count += 1
        except Exception as e:
            log_error(f"Erreur perf P{p_api}/M{m_api}: {e}")

    log_success(f"Performances: {count} nouvelles, {updated} mises à jour.")
    return count + updated

def load_all_data(cleaned_matches, cleaned_players, cleaned_perfs, cleaned_competitions, cleaned_teams):
    """
    Orchestrateur principal du chargement (Pattern Unit of Work).
    """
    session = SessionLocal()
    log_info("💾 Chargement STRICT en base de données...")

    try:
        # 1. Compétitions
        comp_map = load_competitions(session, cleaned_competitions)
        session.flush()

        # 2. Équipes
        team_map = load_teams(session, cleaned_teams, comp_map)
        session.flush()

        # 3. Matchs
        match_map = load_matches(session, cleaned_matches, team_map, comp_map)
        session.flush()

        # 4. Joueurs (Profils Complets)
        player_map = load_players(session, cleaned_players, team_map)
        session.flush()

        # 5. Performances
        load_performances(session, cleaned_perfs, player_map, match_map)
        
        # Validation finale
        session.commit()
        log_success("🎉 Chargement terminé avec succès !")

    except Exception as e:
        session.rollback()
        log_error(f"🔥 ERREUR CHARGEMENT : {e}")
        raise e
    finally:
        session.close()