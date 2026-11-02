from datetime import datetime

def test_read_matches(client, sample_match):
    response = client.get("/api/matches/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_filter_matches_by_status(client, sample_match):
    response = client.get("/api/matches/?status=FT")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    
    response = client.get("/api/matches/?status=NS") # Not Started
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_create_match(client, sample_team_home, sample_team_away, sample_competition):
    payload = {
        "id": 600,
        "date": datetime.now().isoformat(),
        "home_team_id": sample_team_home.id,
        "away_team_id": sample_team_away.id,
        "competition_id": sample_competition.id,
        "status": "NS"
    }
    response = client.post("/api/matches/", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == 600

def test_match_statistics(client, sample_match, sample_performance):
    response = client.get(f"/api/matches/{sample_match.id}/statistics")
    assert response.status_code == 200
    stats = response.json()
    # sample_performance est pour home_team (via sample_player -> sample_team_home)
    assert "home" in stats
    assert stats["home"]["goals"] == 1