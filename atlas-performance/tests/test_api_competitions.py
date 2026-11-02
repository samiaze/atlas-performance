def test_read_competitions(client, sample_competition):
    response = client.get("/api/competitions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test League"

def test_read_competition_by_id(client, sample_competition):
    response = client.get(f"/api/competitions/{sample_competition.id}")
    assert response.status_code == 200
    assert response.json()["season"] == 2024

def test_create_competition(client):
    payload = {
        "id": 99, 
        "name": "New League", 
        "season": 2025, 
        "country": "France"
    }
    response = client.post("/api/competitions/", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "New League"

def test_create_duplicate_competition(client, sample_competition):
    # Tente de créer une compète qui existe déjà (même nom/saison)
    payload = {"id": 102, "name": sample_competition.name, "season": sample_competition.season}
    response = client.post("/api/competitions/", json=payload)
    assert response.status_code == 409

def test_delete_competition(client, sample_competition):
    response = client.delete(f"/api/competitions/{sample_competition.id}")
    assert response.status_code == 204
    # Vérifie qu'elle n'existe plus
    response = client.get(f"/api/competitions/{sample_competition.id}")
    assert response.status_code == 404