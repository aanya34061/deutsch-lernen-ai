import pytest

@pytest.mark.asyncio
async def test_get_dashboard_summary(client):
    response = await client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "current_level" in data
    assert "daily_stats" in data
    assert "skill_scores" in data
    assert "recent_materials" in data
    assert "weak_topics" in data
    assert "vocab_queue" in data
    assert data["daily_stats"]["streak_days"] >= 0
    assert "reading" in data["skill_scores"]
    assert "speaking" in data["skill_scores"]

@pytest.mark.asyncio
async def test_update_learner_level(client):
    # Test valid level update
    response = await client.post("/api/v1/dashboard/level", json={"cefr_level": "A2"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["current_level"] == "A2"

    # Verify updated in dashboard
    dash = await client.get("/api/v1/dashboard")
    assert dash.status_code == 200
    assert dash.json()["current_level"] == "A2"

    # Reset back to A1
    await client.post("/api/v1/dashboard/level", json={"cefr_level": "A1"})

@pytest.mark.asyncio
async def test_invalid_learner_level(client):
    response = await client.post("/api/v1/dashboard/level", json={"cefr_level": "Z9"})
    assert response.status_code == 400
