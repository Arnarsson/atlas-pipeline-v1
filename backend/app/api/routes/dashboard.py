"""Dashboard statistics endpoints."""

from typing import Any

from fastapi import APIRouter

from app.api.routes.pipeline import pipeline_runs
from app.scheduler.tasks import list_connectors

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _summarize_runs(runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Compute high-level stats from in-memory pipeline runs."""
    total_runs = len(runs)

    completed = [run for run in runs.values() if run.get("status") == "completed"]

    def _quality_score(run: dict[str, Any]) -> float:
        results = run.get("results") or {}
        quality = results.get("quality") or {}
        return float(quality.get("overall_score") or 0.0)

    def _pii_count(run: dict[str, Any]) -> int:
        results = run.get("results") or {}
        pii = results.get("pii") or {}
        findings = pii.get("findings") or []
        return len(findings)

    avg_quality_score = (
        sum(_quality_score(run) for run in completed) / len(completed)
        if completed
        else 0.0
    )

    total_pii_detections = sum(_pii_count(run) for run in completed)

    # Surface the 10 most recent runs; in-memory runs don't track time, so use insertion order
    recent_runs = []
    for run_id, run in list(runs.items())[-10:]:
        recent_runs.append(
            {
                "run_id": run_id,
                "dataset_name": run.get("dataset_name"),
                "status": run.get("status"),
                "filename": run.get("filename"),
                "current_step": run.get("current_step"),
                "quality_score": _quality_score(run),
                "pii_detections": _pii_count(run),
                "created_at": run.get("created_at") or run.get("started_at") or "",
                "completed_at": run.get("completed_at") or "",
            }
        )

    return {
        "total_runs": total_runs,
        "avg_quality_score": avg_quality_score,
        "total_pii_detections": total_pii_detections,
        "recent_runs": recent_runs,
    }


@router.get("/stats")
async def get_dashboard_stats() -> dict[str, Any]:
    """Return high-level dashboard statistics."""
    stats = _summarize_runs(pipeline_runs)

    try:
        connectors = list_connectors()
        stats["active_connectors"] = sum(1 for c in connectors if c.get("enabled", True))
    except Exception:
        stats["active_connectors"] = 0

    return stats
