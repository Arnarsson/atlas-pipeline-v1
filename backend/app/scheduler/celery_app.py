"""Celery application for task scheduling and background jobs."""

import os

from celery import Celery
from celery.schedules import crontab

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "atlas_pipeline",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.scheduler.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.scheduler.tasks.*": {"queue": "pipeline"},
    },

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
    },

    # Beat schedule (periodic tasks)
    beat_schedule={
        "sync-all-sources-hourly": {
            "task": "app.scheduler.tasks.sync_all_scheduled_sources",
            "schedule": crontab(minute=0),  # Every hour at :00
        },
        "health-check-connectors": {
            "task": "app.scheduler.tasks.test_connector_health",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
    },
)

# Optional: Configure task time limits
celery_app.conf.task_time_limit = 3600  # 1 hour hard limit
celery_app.conf.task_soft_time_limit = 3000  # 50 minutes soft limit
