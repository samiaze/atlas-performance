def test_dashboard_summary(client, sample_competition, sample_team_home):
    response = client.get("/api/analytics/dashboard-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_competitions"] >= 1
    assert data["total_teams"] >= 1

def test_top_scorers(client, sample_performance):
    response = client.get("/api/analytics/top-scorers?min_matches=1")
    assert response.status_code == 200
    data = response.json()
    # Notre sample_performance a 1 but en 1 match
    assert len(data) >= 1
    assert data[0]["total_goals"] == 1

def test_team_statistics(client, sample_team_home, sample_match):
    # Home Team a gagné 2-1 dans la fixture sample_match
    response = client.get(f"/api/analytics/team-statistics/{sample_team_home.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["wins"] == 1
    assert data["goals_for"] == 2