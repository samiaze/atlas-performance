def test_read_players(client, sample_player):
    response = client.get("/api/players/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_read_player_stats(client, sample_player, sample_performance):
    response = client.get(f"/api/players/{sample_player.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Star Player"
    assert data["total_goals"] == 1
    assert data["total_matches"] == 1

def test_player_performances_history(client, sample_player, sample_performance):
    response = client.get(f"/api/players/{sample_player.id}/performances")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["rating"] == 8.5