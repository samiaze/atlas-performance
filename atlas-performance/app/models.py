from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    season = Column(Integer)
    country = Column(String, nullable=True)
    logo = Column(String, nullable=True)
    flag = Column(String, nullable=True)  # Champ ajouté pour Phase 2
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    matches = relationship("Match", back_populates="competition")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    founded = Column(Integer, nullable=True)
    logo = Column(String, nullable=True)
    venue_name = Column(String, nullable=True)
    venue_city = Column(String, nullable=True)
    
    competition_api_id = Column(Integer, nullable=True) # Champ ajouté pour Phase 2

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    # On spécifie foreign_keys car il y a deux liens vers Team dans Match (home/away)
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    players = relationship("Player", back_populates="team")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), index=True)
    round = Column(String, nullable=True)
    status = Column(String, index=True) # 'FT', 'NS', 'LIVE'
    venue = Column(String, nullable=True)
    referee = Column(String, nullable=True)
    
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    competition_id = Column(Integer, ForeignKey("competitions.id"))
    
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    competition = relationship("Competition", back_populates="matches")
    performances = relationship("Performance", back_populates="match", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    firstname = Column(String, nullable=True)
    lastname = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String, nullable=True)
    height = Column(Integer, nullable=True) # cm
    weight = Column(Integer, nullable=True) # kg
    photo = Column(String, nullable=True)
    
    position = Column(String, nullable=True)
    number = Column(Integer, nullable=True)
    
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    team = relationship("Team", back_populates="players")
    performances = relationship("Performance", back_populates="player")


class Performance(Base):
    __tablename__ = "performances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    
    # Données dénormalisées pour faciliter les requêtes sans jointures
    player_name = Column(String, nullable=True)
    team_api_id = Column(Integer, nullable=True)

    # Stats
    rating = Column(Float, nullable=True)
    minutes_played = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    shots_total = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    passes_total = Column(Integer, default=0)
    passes_accurate = Column(Integer, default=0)
    tackles = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    fouls_committed = Column(Integer, default=0)
    fouls_drawn = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    dribbles_success = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    match = relationship("Match", back_populates="performances")
    player = relationship("Player", back_populates="performances")


class MatchStatistic(Base):
    __tablename__ = "match_statistics"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    shots_total = Column(Integer, default=0)
    shots_on_goal = Column(Integer, default=0)
    shots_off_goal = Column(Integer, default=0)
    shots_blocked = Column(Integer, default=0)
    shots_inside_box = Column(Integer, default=0)
    shots_outside_box = Column(Integer, default=0)
    
    fouls = Column(Integer, default=0)
    corners = Column(Integer, default=0)
    offsides = Column(Integer, default=0)
    ball_possession = Column(String, default="50%") # Souvent en string "50%" ou int
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    goalkeeper_saves = Column(Integer, default=0)
    passes_total = Column(Integer, default=0)
    passes_accurate = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    match = relationship("Match", back_populates="statistics")
    team = relationship("Team")

# Update Match relationship
Match.statistics = relationship("MatchStatistic", back_populates="match", cascade="all, delete-orphan")