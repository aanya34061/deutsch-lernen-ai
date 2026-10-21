import pytest

@pytest.mark.asyncio
async def test_get_levels_catalog(client):
    response = await client.get("/api/v1/levels")
    assert response.status_code == 200
    data = response.json()
    assert "levels" in data
    assert "active_level" in data
    assert data["total_levels"] == 6
    
    # Check that A1 through C2 are present
    codes = [lvl["code"] for lvl in data["levels"]]
    assert codes == ["A1", "A2", "B1", "B2", "C1", "C2"]
    
    # Verify A1 is active with foundational content
    a1 = next(lvl for lvl in data["levels"] if lvl["code"] == "A1")
    assert a1["status"] == "active"
    assert a1["is_available"] is True
    assert len(a1["core_topics"]) > 0
    assert len(a1["grammar_concepts"]) > 0
    assert len(a1["lesson_outlines"]) > 0

    # Verify A1, A2, B1 are active with foundational content in Phase 3
    for active_code in ["A1", "A2", "B1"]:
        lvl = next(l for l in data["levels"] if l["code"] == active_code)
        assert lvl["status"] == "active"
        assert lvl["is_available"] is True
        assert len(lvl["core_topics"]) > 0
        assert len(lvl["grammar_concepts"]) > 0
        assert len(lvl["lesson_outlines"]) > 0

    # Verify B2-C2 are marked as planned / future content
    b2 = next(l for l in data["levels"] if l["code"] == "B2")
    assert b2["status"] == "planned"
    assert b2["is_available"] is False

@pytest.mark.asyncio
async def test_get_single_level_detail(client):
    response = await client.get("/api/v1/levels/A1")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "A1"
    assert "Absolute Beginner" in data["name"]

@pytest.mark.asyncio
async def test_get_nonexistent_level(client):
    response = await client.get("/api/v1/levels/X9")
    assert response.status_code == 404
