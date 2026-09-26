# GeoForraje Backend - Celery App
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "geoforraje",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.raster_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora max por task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    beat_schedule={
        "update-raster-layers-daily": {
            "task": "app.workers.raster_tasks.update_all_raster_layers",
            "schedule": 86400.0,  # Cada 24 horas
        },
    },
)