def test_create_performance_valid(client, sample_match, sample_player):
    # Attention: sample_performance existe déjà pour ce couple, utilisons un autre ID
    # Pour le test, on va supposer qu'on peut créer un autre joueur ou supprimer la perf existante
    client.delete(f"/api/performances/{900}") # Supprime la fixture existante

    payload = {
        "match_id": sample_match.id,
        "player_id": sample_player.id,
        "rating": 7.5,
        "goals": 0,
        "minutes_played": 90
    }
    response = client.post("/api/performances/", json=payload)
    assert response.status_code == 201
    assert response.json()["rating"] == 7.5

def test_create_performance_invalid_rating(client, sample_match, sample_player):
    client.delete(f"/api/performances/{900}")
    
    payload = {
        "match_id": sample_match.id,
        "player_id": sample_player.id,
        "rating": 15.0, # Invalide (> 10)
        "minutes_played": 90
    }
    response = client.post("/api/performances/", json=payload)
    # Pydantic (via field_validator) renvoie 422 Unprocessable Entity
    assert response.status_code == 422