def test_read_teams(client, sample_team_home, sample_team_away):
    response = client.get("/api/teams/")
    assert response.status_code == 200
    assert len(response.json()) >= 2

def test_search_teams(client, sample_team_home):
    response = client.get("/api/teams/?search=Home")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Home FC"

def test_read_team_with_players(client, sample_team_home, sample_player):
    response = client.get(f"/api/teams/{sample_team_home.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Home FC"
    assert len(data["players"]) >= 1
    assert data["players"][0]["name"] == "Star Player"

def test_read_team_matches(client, sample_team_home, sample_match):
    response = client.get(f"/api/teams/{sample_team_home.id}/matches")
    assert response.status_code == 200
    assert len(response.json()) >= 1