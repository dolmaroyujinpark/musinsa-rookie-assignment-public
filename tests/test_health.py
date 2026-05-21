def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["counts"]["students"] >= 10000
    assert data["counts"]["courses"] >= 500
    assert data["counts"]["professors"] >= 100
