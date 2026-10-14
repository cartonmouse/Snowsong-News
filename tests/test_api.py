from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_api_supports_end_to_end_mock_flow(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'api.db'}",
        llm_model="mock",
        news_mode="mock",
        tool_workspace_root=str(tmp_path / "workspace"),
    )
    application = create_app(settings=settings)

    with TestClient(application) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/").status_code == 200

        user_response = client.post(
            "/api/users",
            json={"name": "Alice", "role": "AI engineer"},
        )
        assert user_response.status_code == 200
        user_id = user_response.json()["id"]

        subscription_response = client.put(
            f"/api/users/{user_id}/subscription",
            json={
                "topics": ["agents"],
                "keywords": ["function calling"],
                "sources": ["mock"],
                "push_channel": "history",
            },
        )
        assert subscription_response.status_code == 200

        generation_response = client.post(
            f"/api/users/{user_id}/generate",
        )
        assert generation_response.status_code == 200
        generation = generation_response.json()
        assert generation["status"] == "completed"
        assert generation["brief_id"] is not None
        assert generation["trace"]

        briefs_response = client.get(f"/api/users/{user_id}/briefs")
        assert briefs_response.status_code == 200
        assert len(briefs_response.json()["items"]) == 1
