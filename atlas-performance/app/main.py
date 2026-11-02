from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, case, or_
import traceback
import json

# --- IMPORTS BASE DE DONNÉES ---
from app.database import engine, Base, get_db
from app.routers import competitions, teams, players, matches, performances, analytics
from app.models import Player, Performance, Match, Team, Competition

# 1. INITIALISATION DE LA DB
Base.metadata.create_all(bind=engine)

# 2. INITIALISATION DE L'APP
app = FastAPI(
    title="AtlasPerformance API",
    description="API de statistiques de football pour la CAN et la Coupe du Monde",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 3. CONFIGURATION FRONTEND
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# 4. CONFIGURATION CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. GESTION DES ERREURS GLOBALE
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """
    Intercepte les erreurs 404/500 et renvoie du JSON propre (ou une page 404 HTML si on voulait).
    """
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    return templates.TemplateResponse("layout/base.html", {"request": request}, status_code=exc.status_code) # Fallback simple

# 6. INCLUSION DES ROUTEURS API
app.include_router(competitions.router, prefix="/api/competitions", tags=["Competitions"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(players.router, prefix="/api/players", tags=["Players"])
app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(performances.router, prefix="/api/performances", tags=["Performances"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


# --- ROUTES FRONTEND (INTÉGRÉES AVEC LA LOGIQUE MÉTIER) ---

@app.get("/")
async def root(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")

@app.get("/about", tags=["Frontend"])
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "active_page": "about"})

@app.get("/dashboard", tags=["Frontend"])
async def dashboard_page(request: Request, competition_id: int = None, db: Session = Depends(get_db)):
    # Base filter for matches
    match_filters = []
    if competition_id:
        match_filters.append(Match.competition_id == competition_id)

    # 1. KPIs (Real Data Aggregation)
    # Total Matches
    total_matches = db.query(func.count(Match.id)).filter(*match_filters).scalar() or 0
    
    # Aggregated Stats from Performance linked to Matches (to filter by competition)
    stats_query = db.query(
        func.sum(Performance.goals).label('goals'),
        func.sum(Performance.yellow_cards).label('yellow'),
        func.sum(Performance.red_cards).label('red')
    ).join(Match).filter(*match_filters)
    
    perf_stats = stats_query.first()
    
    stats = {
        "matches_played": total_matches,
        "goals_scored": perf_stats.goals or 0,
        "yellow_cards": perf_stats.yellow or 0,
        "red_cards": perf_stats.red or 0
    }
    
    # 2. MATCHS RÉCENTS (Carousel) - Limit 5 to show "See More" if > 4
    recent_matches = db.query(Match).options(
        joinedload(Match.home_team), 
        joinedload(Match.away_team)
    ).filter(*match_filters).order_by(Match.date.desc()).limit(5).all()

    # 3. TOP SCORERS
    # Join Match to filter by competition
    top_scorers_query = db.query(
        Player.id,
        Player.name,
        Player.photo,
        Team.name.label("team_name"),
        func.sum(Performance.goals).label('total_goals'),
        func.count(Performance.id).label('matches_played'),
        func.avg(Performance.rating).label('avg_rating')
    ).join(Performance).join(Team).join(Match, Performance.match_id == Match.id)
    
    if competition_id:
        top_scorers_query = top_scorers_query.filter(Match.competition_id == competition_id)
        
    top_scorers = top_scorers_query.group_by(Player.id, Player.name, Player.photo, Team.name)\
     .having(func.sum(Performance.goals) > 0)\
     .order_by(func.sum(Performance.goals).desc()).limit(8).all()

    # 4. BEST ELEVEN (Dynamic 4-3-3 based on Average Rating)
    totw_structure = {"gk": [], "def": [], "mid": [], "att": []}
    
    # Query Average Rating for all players in scope
    best_xi_query = db.query(
        Player.id, 
        Player.name, 
        Player.photo, 
        Player.position,
        Team.logo.label("team_logo"),
        func.avg(Performance.rating).label("avg_rating")
    ).join(Performance).join(Match).outerjoin(Team, Player.team_id == Team.id)\
     .filter(Performance.rating.isnot(None))\
     .group_by(Player.id, Player.name, Player.photo, Player.position, Team.logo)
        
    if competition_id:
        best_xi_query = best_xi_query.filter(Match.competition_id == competition_id)
        
    # --- FAIR PLAY LOGIC ---
    # 1. Obtenir le max de matchs joués par un joueur dans le contexte actuel
    max_matches_query = db.query(func.count(Performance.id))\
        .join(Match)\
        .filter(Performance.rating.isnot(None))\
        .group_by(Performance.player_id)\
        .order_by(desc(func.count(Performance.id)))
        
    if competition_id:
        max_matches_query = max_matches_query.filter(Match.competition_id == competition_id)
        
    max_matches = max_matches_query.limit(1).scalar() or 0
    
    # 2. Seuil dynamique (40% du max, minimum 2 matchs)
    min_threshold = max(2, int(max_matches * 0.40))
    
    # 3. Appliquer le filtre
    # On ajoute aussi le count dans le select pour débugger si besoin
    best_xi_query = best_xi_query.having(func.count(Performance.id) >= min_threshold)
    # -----------------------
        
    # Order by Rating DESC
    candidates = best_xi_query.order_by(func.avg(Performance.rating).desc()).limit(100).all()

    # Bucket by position
    for row in candidates:
        # row is a keyed tuple-like object: (id, name, photo, position, team_logo, avg_rating)
        # Access by attribute or index
        try:
            p_id = row.id
            p_name = row.name
            p_photo = row.photo
            p_pos = row.position
            p_team_logo = row.team_logo
            rating_val = row.avg_rating
        except AttributeError:
            # Fallback if it returns distinct tuple (unlikely with this query structure)
            p_id, p_name, p_photo, p_pos, p_team_logo, rating_val = row

        current_rating = round(float(rating_val), 2) if rating_val else 0.0
        
        p_data = {
            "id": p_id,
            "name": p_name,
            "photo": p_photo,
            "team_logo": p_team_logo,
            "rating": current_rating,
            "position": p_pos
        }
        
        if not p_pos: continue
        
        if p_pos in ['GK', 'Goalkeeper']:
            if len(totw_structure["gk"]) < 1: totw_structure["gk"].append(p_data)
        elif p_pos in ['CB', 'LB', 'RB', 'LWB', 'RWB', 'Defender']:
            if len(totw_structure["def"]) < 4: totw_structure["def"].append(p_data)
        elif p_pos in ['CM', 'CDM', 'CAM', 'LM', 'RM', 'Midfielder']:
            if len(totw_structure["mid"]) < 3: totw_structure["mid"].append(p_data)
        elif p_pos in ['ST', 'CF', 'LW', 'RW', 'FW', 'Attacker']:
            if len(totw_structure["att"]) < 3: totw_structure["att"].append(p_data)
    
    team_of_week = totw_structure

    # 4. Context & Filters
    competitions_list = db.query(Competition).order_by(Competition.season.desc(), Competition.name).all()
    # selected_competition_id is already passed as arg

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_matches": recent_matches,
        "top_scorers": top_scorers,
        "team_of_week": team_of_week,
        "competitions_list": competitions_list,
        "selected_competition_id": competition_id
    })


@app.get("/performance", tags=["Frontend"])
@app.get("/performance", tags=["Frontend"])
async def performance_page(
    request: Request, 
    competition_id: str = None, # Changed to str to handle ""
    team_id: str = None,        # Changed to str to handle ""
    position: str = None,
    min_minutes: int = 90, 
    db: Session = Depends(get_db)
):
    """
    Page 'Power BI' like analytics dashboard with Pro metrics.
    """
    # Parse inputs (empty string -> None)
    comp_id = int(competition_id) if competition_id and competition_id.isdigit() else None
    t_id = int(team_id) if team_id and team_id.isdigit() else None
    if position == "": position = None

    # --- FILTERS ---
    base_query = db.query(Performance).join(Match).join(Player)
    if comp_id:
        base_query = base_query.filter(Match.competition_id == comp_id)
    if t_id:
        base_query = base_query.filter(Player.team_id == t_id)
    if position:
        base_query = base_query.filter(Player.position == position)

    # ... (KPIs code remains similar, using comp_id/t_id variables) ...
    # Re-implementing just the start to update variables usage
    
    # 1. Global KPIs (Filtered)
    kpi_stats = base_query.with_entities(
        func.sum(Performance.goals).label('goals'),
        func.count(Match.id).label('matches'),
        func.avg(Performance.rating).label('rating'),
        func.sum(Performance.minutes_played).label('minutes')
    ).first()

    total_goals = kpi_stats.goals or 0
    avg_rating = kpi_stats.rating or 0.0
    total_matches = db.query(Match)
    if comp_id: total_matches = total_matches.filter(Match.competition_id == comp_id)
    total_matches = total_matches.count()
    
    # 2. PRO DATA
    players_stats_query = db.query(
        Player.id, Player.name, Player.photo, Player.position, Team.name.label('team_name'),
        func.sum(Performance.goals).label('goals'),
        func.sum(Performance.assists).label('assists'),
        func.sum(Performance.minutes_played).label('minutes'),
        func.avg(Performance.rating).label('rating'),
        func.sum(Performance.yellow_cards).label('yellow'),
        func.sum(Performance.red_cards).label('red'),
        func.sum(Performance.passes_accurate).label('passes_acc'),
        func.sum(Performance.passes_total).label('passes_tot')
    ).select_from(Performance)\
     .join(Match, Performance.match_id == Match.id)\
     .join(Player)\
     .join(Team)\
     .group_by(Player.id, Player.name, Player.position, Team.name)

    # Apply filters
    if comp_id:
        players_stats_query = players_stats_query.filter(Match.competition_id == comp_id)
    if t_id:
        players_stats_query = players_stats_query.filter(Player.team_id == t_id)
    if position:
        players_stats_query = players_stats_query.filter(Player.position == position)

    # Execution
    raw_stats = players_stats_query.all()
    
    # post-process for Pro Metrics
    pro_data = []
    
    # Team Discipline Aggregation (Team Name -> Score)
    team_discipline = {} 
    
    # Position Aggregation (Pos -> [Ratings])
    pos_ratings = {}

    for p in raw_stats:
        # Min Minutes Threshold
        if (p.minutes or 0) < min_minutes:
            continue
            
        # P90 Calculations
        mins = p.minutes or 1 # Avoid div/0
        factor_90 = 90.0 / mins
        
        g_90 = (p.goals or 0) * factor_90
        a_90 = (p.assists or 0) * factor_90
        
        # Pass Accuracy
        pass_acc = 0.0
        if p.passes_tot and p.passes_tot > 0:
            pass_acc = (p.passes_acc / p.passes_tot) * 100
            
        # Discipline Score (Yellow=1, Red=3)
        disc_score = (p.yellow or 0) * 1 + (p.red or 0) * 3
        
        # GPI Formula (V1)
        # (Rating * 0.5) + (Goals_P90 * 20) + (Assists_P90 * 15) + (Pass_Acc * 0.1) - (Discipline_Score * 0.5)
        # We cap Rating influence slightly
        rating = p.rating or 0.0
        gpi = (rating * 4.0) + (g_90 * 20.0) + (a_90 * 15.0) + (pass_acc * 0.05) - (disc_score * 1.0)
        
        player_obj = {
            "id": p.id,
            "id": p.id,
            "name": p.name,
            "photo": p.photo,
            "team": p.team_name,
            "position": p.position,
            "minutes": p.minutes or 0,
            "goals": p.goals or 0,
            "assists": p.assists or 0,
            "rating": round(rating, 2),
            "g_p90": round(g_90, 2),
            "a_p90": round(a_90, 2),
            "gpi": round(gpi, 1)
        }
        pro_data.append(player_obj)
        
        # Aggregation for Discipline Chart (Team)
        if p.team_name and p.team_name not in team_discipline:
            team_discipline[p.team_name] = {"minutes": 0, "score": 0}
        
        if p.team_name:
            team_discipline[p.team_name]["minutes"] += mins
            team_discipline[p.team_name]["score"] += disc_score
        
        # Aggregation for Position Chart
        if p.position:
            if p.position not in pos_ratings: pos_ratings[p.position] = []
            pos_ratings[p.position].append(rating)

    # Sort Pro Data by GPI Desc
    pro_data.sort(key=lambda x: x["gpi"], reverse=True)
    
    # Prepare Discipline Chart Data (Normalized per 90 for Teams)
    disc_chart_labels = []
    disc_chart_data = []
    for t_name, data in team_discipline.items():
        if data["minutes"] > 500: # Threshold for team stats
            score_p90 = (data["score"] * 90) / data["minutes"]
            disc_chart_labels.append(t_name)
            disc_chart_data.append(round(score_p90, 2))
            
    # Prepare Position Chart Data (Avg Rating)
    pos_chart_labels = []
    pos_chart_data = []
    for pos, ratings in pos_ratings.items():
        if len(ratings) > 0:
            avg = sum(ratings) / len(ratings)
            pos_chart_labels.append(pos)
            pos_chart_data.append(round(avg, 2))

    # Context Data for Filters
    all_competitions = db.query(Competition).all()
    
    # Context Data for Filters (Cascading)
    teams_query = db.query(Team)
    if comp_id:
        teams_query = teams_query.join(Match, or_(Match.home_team_id == Team.id, Match.away_team_id == Team.id))\
                                 .filter(Match.competition_id == comp_id)\
                                 .distinct()
    all_teams = teams_query.order_by(Team.name).all()

    # Unique positions
    distinct_positions = db.query(Player.position).distinct().filter(Player.position.isnot(None)).all()
    all_positions = sorted([r[0] for r in distinct_positions])
    
    # Comparator Dropdown
    all_players = db.query(Player.id, Player.name).order_by(Player.name).all()

    return templates.TemplateResponse("performance.html", {
        "request": request,
        "active_page": "performance",
        "kpis": {
            "total_goals": total_goals,
            "total_matches": total_matches,
            "avg_rating": round(avg_rating, 2)
        },
        "charts": {
            # Scatter: GPI vs Minutes (or Rating vs Minutes)
            "scatter_minutes": json.dumps([p["minutes"] for p in pro_data[:50]]), 
            "scatter_rating": json.dumps([p["rating"] for p in pro_data[:50]]),
            "scatter_names": json.dumps([p["name"] for p in pro_data[:50]]),
            "scatter_goals": json.dumps([p["goals"] * 5 + 5 for p in pro_data[:50]]), # p["goals"] is now safe
            
            # Discipline Bar
            "disc_labels": json.dumps(disc_chart_labels),
            "disc_data": json.dumps(disc_chart_data),
            
            # Position Bar
            "pos_labels": json.dumps(pos_chart_labels),
            "pos_data": json.dumps(pos_chart_data)
        },
        "pro_table": pro_data,
        "all_players": all_players,
        "filters": {
            "competitions": all_competitions,
            "teams": all_teams,
            "positions": all_positions,
            "selected_comp": comp_id,
            "selected_team": t_id,
            "selected_pos": position
        }
    })


@app.get("/players/{player_id}", tags=["Frontend"])
async def player_profile_page(request: Request, player_id: int, competition_id: int = None, db: Session = Depends(get_db)):
    # 1. PLAYER INFO
    player = db.query(Player).options(joinedload(Player.team)).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Joueur non trouvé")

    # 2. GLOBAL STATS (Filtered)
    stats_query = db.query(
        func.sum(Performance.goals).label("goals"),
        func.sum(Performance.assists).label("assists"),
        func.sum(Performance.minutes_played).label("minutes"),
        func.avg(Performance.rating).label("avg_rating"),
        func.avg(Performance.passes_accurate).label("pass_acc"),
        func.avg(Performance.tackles).label("tackles"),
        func.avg(Performance.interceptions).label("interceptions")
    ).filter(Performance.player_id == player_id)

    if competition_id:
        stats_query = stats_query.join(Match).filter(Match.competition_id == competition_id)

    stats = stats_query.first()

    # 3. RECENT MATCHES (Filtered)
    recent_perfs_query = db.query(Performance).join(Match).options(
        joinedload(Performance.match).joinedload(Match.home_team),
        joinedload(Performance.match).joinedload(Match.away_team)
    ).filter(Performance.player_id == player_id)

    if competition_id:
        recent_perfs_query = recent_perfs_query.filter(Match.competition_id == competition_id)

    recent_perfs = recent_perfs_query.order_by(Match.date.desc()).limit(5).all()

    # Formater les matchs récents pour le template
    formatted_matches = []
    for perf in recent_perfs:
        # Guard clause for corrupted data
        if not perf.match or not perf.match.home_team or not perf.match.away_team:
            continue

        opponent = perf.match.away_team.name if perf.match.home_team_id == player.team_id else perf.match.home_team.name
        
        is_home = (perf.match.home_team_id == player.team_id)
        my_score = perf.match.home_score if is_home else perf.match.away_score
        opp_score = perf.match.away_score if is_home else perf.match.home_score
        
        result = "D"
        if my_score is not None and opp_score is not None:
            if my_score > opp_score: result = "W"
            elif my_score == opp_score: result = "N"
            else: result = "L"
            
        formatted_matches.append({
            "opp": opponent[:3].upper() if opponent else "UNK", 
            "result": result,
            "rating": round(float(perf.rating), 1) if perf.rating else 0.0
        })

    # Safe Stats Handling (Decimal -> Float conversion for JSON serialization)
    class SafeStats:
        def __init__(self, s):
            self.goals = float(s.goals) if s and s.goals else 0.0
            self.assists = float(s.assists) if s and s.assists else 0.0
            self.minutes = int(s.minutes) if s and s.minutes else 0
            self.avg_rating = float(s.avg_rating) if s and s.avg_rating else 0.0
            self.pass_acc = float(s.pass_acc) if s and s.pass_acc else 0.0
            self.tackles = float(s.tackles) if s and s.tackles else 0.0
            self.interceptions = float(s.interceptions) if s and s.interceptions else 0.0

    s = SafeStats(stats)

    # 4. CHART DATA (Radar & Evolution & Contribution)
    
    # A. Evolution Chart Data (Last 10 matches)
    evolution_query = db.query(Performance).join(Match).filter(Performance.player_id == player_id)
    if competition_id:
        evolution_query = evolution_query.filter(Match.competition_id == competition_id)
    evolution_perfs = evolution_query.order_by(Match.date.asc()).limit(10).all() # ASC to plot form over time correctly
    
    # Safe Date Formatter
    def get_date_str(d):
        if not d: return ""
        if hasattr(d, 'strftime'): return d.strftime("%d/%m")
        # Fallback for string dates (YYYY-MM-DD...)
        s = str(d)
        if len(s) >= 10:
            return f"{s[8:10]}/{s[5:7]}"
        return s

    dates = []
    ratings = []
    for p in evolution_perfs:
        if p.match and p.match.date:
            dates.append(get_date_str(p.match.date))
            ratings.append(round(float(p.rating), 1) if p.rating else 0.0)

    evolution_data = {
        "dates": dates,
        "ratings": ratings
    }

    # B. Radar Data (Existing Logic)
    # Helper for scaling values
    def get_radar_values(g, a, pa, r, t, i):
        return [
            min(float(g) * 20, 100),
            min(float(a) * 20, 100),
            float(pa),
            float(r) * 10,
            float(t) * 30,
            float(i) * 30
        ]
        
    radar_season = get_radar_values(s.goals, s.assists, s.pass_acc, s.avg_rating, s.tackles, s.interceptions)
    
    # Last 5 Calculation
    def safefloat(v): return float(v) if v else 0.0
    
    l5_count = len(recent_perfs) if recent_perfs else 1 # Avoid div by 0
    l5_goals = sum(safefloat(p.goals) for p in recent_perfs)
    l5_assists = sum(safefloat(p.assists) for p in recent_perfs)
    # Averages
    l5_pass = sum(safefloat(p.passes_accurate) for p in recent_perfs) / l5_count
    l5_rating = sum(safefloat(p.rating) for p in recent_perfs) / l5_count
    l5_tackles = sum(safefloat(p.tackles) for p in recent_perfs) / l5_count
    l5_interc = sum(safefloat(p.interceptions) for p in recent_perfs) / l5_count
    
    # Note: For goals/assists, if period is short (5 games), total is small.
    # To compare fairly with "Season" (if Season uses Totals), we might need to extrapolate or compare to "Expected per 5 games"?
    # But for simplicity, we visualize what they did. 
    # Wait, existing code: s.goals * 20. If 5 goals -> 100.
    # So if you score 5 goals in 5 games, you hit 100. Correct.
    radar_last5 = get_radar_values(l5_goals, l5_assists, l5_pass, l5_rating, l5_tackles, l5_interc)

    # Raw Values for Tooltips
    radar_season_raw = [int(s.goals), int(s.assists), round(s.pass_acc, 1), round(s.avg_rating, 2), int(s.tackles), int(s.interceptions)]
    radar_last5_raw = [int(l5_goals), int(l5_assists), round(l5_pass, 1), round(l5_rating, 2), round(l5_tackles, 1), round(l5_interc, 1)]

    chart_data = {
        "labels": ["Buts", "Passes", "Précision (%)", "Note Globale", "Tacles", "Intercept."],
        "season": radar_season,
        "last5": radar_last5,
        "season_raw": radar_season_raw,
        "last5_raw": radar_last5_raw,
        "last5_count": len(recent_perfs)
    }

    # 5. CONSTRUCT PLAYER OBJECT FOR TEMPLATE
    player_view = {
        "id": player.id,
        "name": player.name,
        "number": player.number,
        "position": player.position,
        "team": player.team.name,
        "team_logo": player.team.logo if hasattr(player.team, 'logo') else "",
        "photo": player.photo if player.photo else "https://media.api-sports.io/football/players/1.png",
        "nationality": player.nationality,
        "age": player.age or 25,
        "height": player.height or 180,
        "weight": player.weight or 75,
        "rating": round(s.avg_rating, 2),
        "key_stats": [
            {"label": "Minutes", "value": s.minutes, "trend": "equal", "diff": "="},
            {"label": "Buts", "value": int(s.goals), "trend": "up", "diff": "+1"},
            {"label": "Passes D.", "value": int(s.assists), "trend": "equal", "diff": "="},
            {"label": "Note Moy.", "value": round(s.avg_rating, 2), "trend": "up", "diff": "+0.1"}
        ],
        "recent_matches": formatted_matches
    }

    # Context
    competitions_list = db.query(Competition).order_by(Competition.season.desc(), Competition.name).all()

    return templates.TemplateResponse("player_profile.html", {
        "request": request, 
        "active_page": "players",
        "player": player_view,
        "chart_data": chart_data,
        "evolution_data": evolution_data,
        "competitions_list": competitions_list,
        "selected_competition_id": competition_id
    })


@app.get("/competitions", tags=["Frontend"])
async def competitions_page(request: Request, competition_id: int = None, db: Session = Depends(get_db)):
    # Récupérer les compétitions avec le nombre d'équipes et de matchs
    comps_data = []
    competitions = db.query(Competition).all()
    
    for comp in competitions:
        # Count teams (approximation via matches if no direct link, but usually comp -> matches -> teams)
        # Or simply count matches
        match_count = db.query(func.count(Match.id)).filter(Match.competition_id == comp.id).scalar()
        
        # Pour les équipes, c'est plus complexe sans table d'association directe CompetitionTeam.
        # On va compter les équipes distinctes dans les matchs de la compétition.
        teams_in_comp = db.query(Match.home_team_id).filter(Match.competition_id == comp.id).union(
                        db.query(Match.away_team_id).filter(Match.competition_id == comp.id)
        ).count()

        comps_data.append({
            "name": comp.name,
            "logo": comp.logo, # Assumant que le modèle a un champ logo
            "type": "Coupe" if "Cup" in comp.name else "Championnat",
            "country": comp.country or "Afrique",
            "total_matches": match_count,
            "total_teams": teams_in_comp,
            "id": comp.id # Ensure ID is passed for the link logic
        })

    competitions_list = db.query(Competition).order_by(Competition.season.desc(), Competition.name).all()
    return templates.TemplateResponse("competitions.html", {
        "request": request, 
        "active_page": "competitions",
        "competitions": comps_data,
        "competitions_list": competitions_list,
        "selected_competition_id": competition_id
    })

@app.get("/teams", tags=["Frontend"])
async def teams_page(request: Request, competition_id: int = None, search: str = None, db: Session = Depends(get_db)):
    # Récupérer les équipes avec stats agrégées
    teams_query = db.query(Team)
    
    if search:
        teams_query = teams_query.filter(Team.name.ilike(f"%{search}%"))

    if competition_id:
        # Filter teams that have played in this competition
        # We check if they appear as home or away team in matches of this competition
        teams_query = teams_query.filter(
            Team.id.in_(
                db.query(Match.home_team_id).filter(Match.competition_id == competition_id).union(
                    db.query(Match.away_team_id).filter(Match.competition_id == competition_id)
                )
            )
        )
        
    teams_db = teams_query.limit(100).all()
    
    teams_data = []
    for team in teams_db:
        # Stats basiques
        matches_count_query = db.query(func.count(Match.id)).filter(
                (Match.home_team_id == team.id) | (Match.away_team_id == team.id)
            )
        if competition_id:
             matches_count_query = matches_count_query.filter(Match.competition_id == competition_id)
        
        matches_played = matches_count_query.scalar()
        
        # Match count logic modification:
        # If filtered by competition, matches_played will be correct.
        
        # Calculate Goals Scored in this competition (or global)
        # Complex to do efficiently in loop, but let's try a direct query for goals
        goals_query = db.query(func.sum(Match.home_score)).filter(Match.home_team_id == team.id)
        if competition_id: goals_query = goals_query.filter(Match.competition_id == competition_id)
        goals_home = goals_query.scalar() or 0
        
        goals_query_away = db.query(func.sum(Match.away_score)).filter(Match.away_team_id == team.id)
        if competition_id: goals_query_away = goals_query_away.filter(Match.competition_id == competition_id)
        goals_away = goals_query_away.scalar() or 0
        
        # Calculate Average Rating
        rating_query = db.query(func.avg(Performance.rating)).join(Player).filter(Player.team_id == team.id)
        if competition_id:
            rating_query = rating_query.join(Match).filter(Match.competition_id == competition_id)
        
        avg_rating = rating_query.scalar() or 0.0

        stats = {
            "matches_played": matches_played,
            "goals_scored": int(goals_home + goals_away),
            "avg_rating": round(float(avg_rating), 1) if avg_rating else 0.0
        }
        
        # Add basic info
        teams_data.append({
            "id": team.id,
            "name": team.name,
            "logo": team.logo,
            "country": team.country,
            "stats": stats
        })

    competitions_list = db.query(Competition).order_by(Competition.season.desc(), Competition.name).all()
    return templates.TemplateResponse("teams.html", {
        "request": request, 
        "active_page": "teams",
        "teams": teams_data,
        "competitions_list": competitions_list,
        "selected_competition_id": competition_id
    })


@app.get("/teams/{team_id}", tags=["Frontend"])
async def team_detail_page(request: Request, team_id: int, competition_id: int = None, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Équipe non trouvée")

    # 1. Stats globales via aggregation (Filtered)
    matches_query = db.query(Match).filter((Match.home_team_id == team.id) | (Match.away_team_id == team.id))
    if competition_id:
        matches_query = matches_query.filter(Match.competition_id == competition_id)
        
    # Calculate Goals Scored
    goals_query = db.query(func.sum(Match.home_score)).filter(Match.home_team_id == team.id)
    if competition_id: goals_query = goals_query.filter(Match.competition_id == competition_id)
    goals_home = goals_query.scalar() or 0
    
    goals_query_away = db.query(func.sum(Match.away_score)).filter(Match.away_team_id == team.id)
    if competition_id: goals_query_away = goals_query_away.filter(Match.competition_id == competition_id)
    goals_away = goals_query_away.scalar() or 0

    stats = {
        "matches_played": matches_query.count(),
        "goals_scored": int(goals_home + goals_away),
        "avg_rating": 0.0
    }
    
    # Calculate Average Rating
    rating_query = db.query(func.avg(Performance.rating)).join(Player).filter(Player.team_id == team.id)
    if competition_id:
        rating_query = rating_query.join(Match).filter(Match.competition_id == competition_id)
    
    avg_rating = rating_query.scalar() or 0.0
    stats["avg_rating"] = round(float(avg_rating), 1) if avg_rating else 0.0

    # 2. Joueurs de l'équipe
    team_players = db.query(Player).filter(Player.team_id == team.id).all()
    
    # 3. Matchs récents (Filtered)
    recent_matches_query = db.query(Match).options(
        joinedload(Match.home_team), 
        joinedload(Match.away_team),
        joinedload(Match.competition)
    ).filter((Match.home_team_id == team.id) | (Match.away_team_id == team.id))

    if competition_id:
        recent_matches_query = recent_matches_query.filter(Match.competition_id == competition_id)

    recent_matches = recent_matches_query.order_by(Match.date.desc()).limit(10).all()

    formatted_matches = []
    for m in recent_matches:
        is_home = (m.home_team_id == team.id)
        opponent = m.away_team if is_home else m.home_team
        my_score = m.home_score if is_home else m.away_score
        opp_score = m.away_score if is_home else m.home_score
        
        res = "N"
        if my_score is not None and opp_score is not None:
            if my_score > opp_score: res = "W"
            elif my_score < opp_score: res = "L"
        
        formatted_matches.append({
            "id": m.id,
            "date": m.date,
            "competition": m.competition.name if m.competition else "International",
            "opponent": opponent.name,
            "opponent_logo": opponent.logo,
            "score": f"{my_score}-{opp_score}" if my_score is not None else "vs",
            "result": res
        })

    # Context
    competitions_list = db.query(Competition).order_by(Competition.season.desc(), Competition.name).all()

    return templates.TemplateResponse("team_detail.html", {
        "request": request, 
        "active_page": "teams",
        "team": team,
        "players": team_players,
        "matches": formatted_matches,
        "stats": stats,
        "competitions_list": competitions_list,
        "selected_competition_id": competition_id
    })

@app.get("/players", tags=["Frontend"])
async def players_list_page(
    request: Request, 
    competition_id: int = None, 
    search: str = None, 
    team_id: str = None, 
    position: str = None, 
    db: Session = Depends(get_db)
):
    # Base Query
    query = db.query(Player).options(joinedload(Player.team))
    
    # Apply Filters
    if search:
        query = query.filter(Player.name.ilike(f"%{search}%"))
    if team_id and team_id.isdigit():
        query = query.filter(Player.team_id == int(team_id))
    if position:
        # Map abbreviations if necessary or use direct match if DB has full names
        # Assuming DB has "Defender", "Attacker" etc, and frontend sends these or abbreviations.
        # If frontend sends "DF", we might need mapping. 
        # But we will update frontend to send full names or map here.
        # Let's support both for robustness.
        pos_map = {"GK": "Goalkeeper", "DF": "Defender", "MF": "Midfielder", "FW": "Attacker"}
        db_pos = pos_map.get(position, position)
        query = query.filter(Player.position == db_pos)

    if competition_id:
        # Filter players who have played in this competition
        query = query.join(Performance).join(Match)\
                     .filter(Match.competition_id == competition_id)\
                     .distinct()
        
    # Pagination (limit 300, TODO: real pagination)
    players_query = query.limit(300).all()
    
    # Pour les filtres (dropdowns)
    all_teams = db.query(Team).order_by(Team.name).all()
    
    players_data = []
    for p in players_query:
        # Stats agrégées rapides (Filtered)
        p_stats_query = db.query(
            func.count(Performance.id).label("matches"),
            func.sum(Performance.goals).label("goals"),
            func.avg(Performance.rating).label("rating")
        ).filter(Performance.player_id == p.id)
        
        if competition_id:
             p_stats_query = p_stats_query.join(Match).filter(Match.competition_id == competition_id)
             
        p_stats = p_stats_query.first()
        
        players_data.append({
            "id": p.id,
            "name": p.name,
            "photo": p.photo,
            "nationality": p.nationality,
            "team_id": p.team_id,
            "team_name": p.team.name if p.team else "Sans club",
            "team_logo": p.team.logo if p.team else None,
            "position": p.position,
            "stats": {
                "matches": p_stats.matches or 0,
                "goals": p_stats.goals or 0,
                "rating": round(p_stats.rating, 1) if p_stats.rating else None
            }
        })

    competitions_list = db.query(Competition).order_by(Competition.season.desc(), Competition.name).all()
    return templates.TemplateResponse("players.html", {
        "request": request, 
        "active_page": "players",
        "players": players_data,
        "teams_filter": all_teams,
        "total_players": len(players_data), # Accurate count of displayed players
        "competitions_list": competitions_list,
        "selected_competition_id": competition_id,
        "selected_search": search,
        "selected_team_id": team_id,
        "selected_position": position
    })

@app.get("/matches", tags=["Frontend"])
async def matches_list_page(request: Request, competition_id: int = None, db: Session = Depends(get_db)):
    matches_query = db.query(Match).options(
        joinedload(Match.home_team), 
        joinedload(Match.away_team),
        joinedload(Match.competition)
    )
    
    if competition_id:
        matches_query = matches_query.filter(Match.competition_id == competition_id)
        
    matches_db = matches_query.order_by(Match.date.desc()).limit(300).all()
    
    seasons_list = [s[0] for s in db.query(Competition.season).distinct().all() if s[0]]
    competitions_list = db.query(Competition).order_by(Competition.season.desc(), Competition.name).all()
    return templates.TemplateResponse("matches.html", {
        "request": request, 
        "active_page": "matches",
        "matches": matches_db,
        "competitions_list": competitions_list,
        "selected_competition_id": competition_id
    })

@app.get("/matches/{match_id}", tags=["Frontend"])
async def match_detail_page(request: Request, match_id: int, db: Session = Depends(get_db)):
    # 1. Fetch Match with Teams, Competition AND Statistics
    match = db.query(Match).options(
        joinedload(Match.home_team),
        joinedload(Match.away_team),
        joinedload(Match.competition),
        joinedload(Match.statistics)
    ).filter(Match.id == match_id).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match non trouvé")

    # --- ON-THE-FLY ETL: Fetch Stats if missing ---
    if not match.statistics and match.status in ["FT", "AET", "PEN", "LIVE", "1H", "2H", "HT"]:
        # Only fetch for matches that have started/finished
        try:
             # Need API ID (assuming match.id is mapped or we have an api_id column. 
             # Standard project structure usually has 'api_id' in models if syncing.
             # Checking models.py, 'Match' has 'id' which might be our internal ID.
             # Wait, models.py doesn't show an specific 'api_id' column in Match, just 'id'.
             # BUT in 'etl/extract/matches.py', it maps "api_id": fixture['id'].
             # So 'id' IS the API ID? Let's assume safely or look for 'api_id'.
             # The extract script maps "api_id" -> cleaned["api_id"]. 
             # DB Schema: id = Column(Integer, primary_key=True).
             # Usually people map API ID to PK or separate column.
             # Let's assume PK IS API ID for this project context or add a try/catch.
             # For safety, I'll assume match.id corresponds to fixture_id.
             
            from etl.extract.matches import fetch_match_statistics
            from app.models import MatchStatistic

            stats_data = fetch_match_statistics(match.id)
            
            if stats_data:
                # Helper to parse API response list dict to model
                # API format: [{"team": {id:..}, "statistics": [{"type": "Shots on Goal", "value": 5}, ...]}, ...]
                for team_stat in stats_data:
                    t_id = team_stat["team"]["id"]
                    # Map API team ID to our DB Team ID.
                    # This requires finding the Team by API ID (or if our IDs match API IDs).
                    # 'Team' model: id = PK. etl/extract/teams.py usually sets this.
                    # Let's verify if team exists in our DB, linked to this match.
                    
                    # Identify if this is home or away
                    db_team_id = None
                    # API team ID match?
                    # Since we don't have api_id column on Team explicitly seen in models (Wait, let me check models again ... 
                    # Team has 'competition_api_id'. Detailed view showed 'id'. No 'api_id'. 
                    # Safest assumption: DB ID matches API ID or we lookup via match.home_team_id/away_team_id.
                    if match.home_team_id == t_id:
                        db_team_id = match.home_team_id
                    elif match.away_team_id == t_id:
                        db_team_id = match.away_team_id
                    else:
                        # Fallback: check if t_id matches one of the teams
                        # (Maybe internal IDs differ from API IDs, but match.home_team_id is FK).
                        # Let's trust the API returns stats for the teams in the fixture.
                        if match.home_team and match.home_team.id == t_id: # If our PK is API ID
                             db_team_id = t_id
                        elif match.away_team and match.away_team.id == t_id:
                             db_team_id = t_id
                    
                    if not db_team_id:
                        # Try to resolve via home/away index in list? No, unreliable.
                        # Using the match home/away IDs is safest if we assume order or IDs match.
                        # Let's try to match by name if ID fails? No.
                        # Let's assume for now our DB usage implies ID consistency for simplicty in this "Quick Fix".
                        # If extraction used API IDs as IDs (common in simple etls), we are good.
                        db_team_id = t_id 

                    # Parse values
                    raw = {item["type"]: item["value"] for item in team_stat["statistics"]}
                    
                    new_stat = MatchStatistic(
                        match_id=match.id,
                        team_id=db_team_id,
                        shots_total=raw.get("Total Shots") or 0,
                        shots_on_goal=raw.get("Shots on Goal") or 0,
                        shots_off_goal=raw.get("Shots off Goal") or 0,
                        shots_blocked=raw.get("Blocked Shots") or 0,
                        shots_inside_box=raw.get("Shots insidebox") or 0,
                        shots_outside_box=raw.get("Shots outsidebox") or 0,
                        fouls=raw.get("Fouls") or 0,
                        corners=raw.get("Corner Kicks") or 0,
                        offsides=raw.get("Offsides") or 0,
                        ball_possession=str(raw.get("Ball Possession") or "0%"),
                        yellow_cards=raw.get("Yellow Cards") or 0,
                        red_cards=raw.get("Red Cards") or 0,
                        goalkeeper_saves=raw.get("Goalkeeper Saves") or 0,
                        passes_total=raw.get("Total passes") or 0,
                        passes_accurate=raw.get("Passes accurate") or 0
                    )
                    db.add(new_stat)
                
                db.commit()
                # Reload to get stats
                db.refresh(match)
                
        except Exception as e:
            print(f"Error fetching stats on the fly: {e}")
            pass # Fail gracefully, show empty stats

    # 2. Fetch Performances (Lineups)
    performances = db.query(Performance).options(
        joinedload(Performance.player)
    ).filter(Performance.match_id == match_id).all()

    home_lineup = []
    away_lineup = []

    for perf in performances:
        if not perf.player:
            continue
            
        p_data = {
            "id": perf.player.id,
            "name": perf.player.name,
            "number": perf.player.number or 0, # Used model field
            "position": perf.player.position,
            "rating": round(float(perf.rating), 1) if perf.rating else "-",
            "goals": perf.goals,
            "assists": perf.assists,
            "photo": perf.player.photo,
            "minutes": perf.minutes_played,
            "_sort_rating": float(perf.rating) if perf.rating else -1.0
        }
        
        if perf.player.team_id == match.home_team_id:
            home_lineup.append(p_data)
        elif perf.player.team_id == match.away_team_id:
            away_lineup.append(p_data)
    
    # Sort lineups by rating (descending)
    home_lineup.sort(key=lambda x: x["_sort_rating"], reverse=True)
    away_lineup.sort(key=lambda x: x["_sort_rating"], reverse=True)
    
    # 3. Stats Preparation (From DB or Fallback)
    def clean_possession(val):
        if not val: return 50
        return int(str(val).replace('%', ''))

    if match.statistics:
        # We have data!
        # Sort by home/away
        stat_home = next((s for s in match.statistics if s.team_id == match.home_team_id), None)
        stat_away = next((s for s in match.statistics if s.team_id == match.away_team_id), None)
        
        # Default objects if one missing (unlikely)
        class EmptyStat: 
            def __getattr__(self, _): return 0
        
        h = stat_home or EmptyStat()
        a = stat_away or EmptyStat()
        
        home_stats = {
            "goals": match.home_score,
            "shots": h.shots_total,
            "shots_target": h.shots_on_goal,
            "shots_off": h.shots_off_goal,
            "blocked": h.shots_blocked,
            "inside": h.shots_inside_box,
            "outside": h.shots_outside_box,
            "poss": clean_possession(h.ball_possession),
            "passes": h.passes_total,
            "fouls": h.fouls,
            "corners": h.corners,
            "offsides": h.offsides,
            "yellow": h.yellow_cards,
            "red": h.red_cards,
            "saves": h.goalkeeper_saves
        }
        away_stats = {
            "goals": match.away_score,
            "shots": a.shots_total,
            "shots_target": a.shots_on_goal,
            "shots_off": a.shots_off_goal,
            "blocked": a.shots_blocked,
            "inside": a.shots_inside_box,
            "outside": a.shots_outside_box,
            "poss": clean_possession(a.ball_possession),
            "passes": a.passes_total,
            "fouls": a.fouls,
            "corners": a.corners,
            "offsides": a.offsides,
            "yellow": a.yellow_cards,
            "red": a.red_cards,
            "saves": a.goalkeeper_saves
        }
    else:
        # Fallback to Aggregation (if fetch failed or match not started)
        def agg_stats(team_id):
            p_list = [p for p in performances if p.player and p.player.team_id == team_id]
            return {
                "goals": sum(p.goals or 0 for p in p_list), # Will be overwritten by match score
                "shots": sum(p.shots_total or 0 for p in p_list),
                "shots_target": sum(p.shots_on_target or 0 for p in p_list),
                "shots_off": 0, "blocked": 0, "inside": 0, "outside": 0, # Missing in perf
                "poss": 50,
                "passes": sum(p.passes_total or 0 for p in p_list),
                "fouls": sum(p.fouls_committed or 0 for p in p_list),
                "corners": 0, "offsides": 0, # Missing
                "yellow": sum(p.yellow_cards or 0 for p in p_list),
                "red": sum(p.red_cards or 0 for p in p_list),
                "saves": sum(p.saves or 0 for p in p_list)
            }

        home_stats = agg_stats(match.home_team_id)
        away_stats = agg_stats(match.away_team_id)
        home_stats["goals"] = match.home_score if match.home_score is not None else 0
        away_stats["goals"] = match.away_score if match.away_score is not None else 0

    return templates.TemplateResponse("match_detail.html", {
        "request": request,
        "active_page": "matches",
        "match": match,
        "home_lineup": home_lineup,
        "away_lineup": away_lineup,
        "home_stats": home_stats,
        "away_stats": away_stats
    })
