"""Scheduler components for automated pipeline execution."""

from app.scheduler.celery_app import celery_app

__all__ = ["celery_app"]
