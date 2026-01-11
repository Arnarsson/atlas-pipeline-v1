from app.api.routes.pipeline import pipeline_runs
from fastapi.testclient import TestClient


def test_dashboard_stats_empty(client: TestClient) -> None:
    pipeline_runs.clear()

    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200

    data = response.json()
    assert data["total_runs"] == 0
    assert data["avg_quality_score"] == 0
    assert data["total_pii_detections"] == 0
    assert data["recent_runs"] == []
    assert data["active_connectors"] == 0


def test_dashboard_stats_with_completed_run(client: TestClient) -> None:
    pipeline_runs.clear()
    pipeline_runs["run-1"] = {
        "run_id": "run-1",
        "status": "completed",
        "dataset_name": "dataset_a",
        "filename": "file.csv",
        "current_step": "completed",
        "results": {
            "quality": {"overall_score": 0.8},
            "pii": {"findings": [{"column": "email", "type": "EMAIL_ADDRESS"}]},
        },
    }

    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_runs"] == 1
    assert data["avg_quality_score"] == 0.8
    assert data["total_pii_detections"] == 1
    assert len(data["recent_runs"]) == 1
    assert data["recent_runs"][0]["run_id"] == "run-1"
