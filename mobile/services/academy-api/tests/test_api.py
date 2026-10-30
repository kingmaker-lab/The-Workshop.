from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_games_and_challenges():
    assert len(client.get("/api/v1/games").json()) == 2
    challenges = client.get("/api/v1/challenges").json()
    assert len(challenges) == 5
    assert all("answer" not in c and "explanation" not in c for c in challenges)
    assert len(client.get("/api/v1/challenges?game_id=debug").json()) == 2


def test_detail_redacts_answer():
    response = client.get("/api/v1/challenges/logic-001")
    assert response.status_code == 200
    assert "answer" not in response.json()


def test_check_correct_and_wrong():
    url = "/api/v1/challenges/logic-001/check"
    assert client.post(url, json={"choice_id": "a"}).json()["correct"] is True
    assert client.post(url, json={"choice_id": "b"}).json()["correct"] is False


def test_invalid_payload_and_unknown_ids():
    assert client.get("/api/v1/challenges/missing").status_code == 404
    assert client.get("/api/v1/challenges?game_id=missing").status_code == 404
    assert client.post("/api/v1/challenges/logic-001/check", json={"choice_id": "!!"}).status_code == 422
    assert client.post("/api/v1/challenges/logic-001/check", json={"choice_id": "z"}).status_code == 422


def test_cors_disallows_untrusted_origin():
    res = client.get("/api/v1/games", headers={"Origin": "https://untrusted.example"})
    assert "access-control-allow-origin" not in res.headers
