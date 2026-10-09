# Celery App para tareas de análisis raster
from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "geoforraje",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.raster_tasks",
        "app.workers.periodic_tasks",
    ],
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
    # Configuración de colas
    task_routes={
        "app.workers.raster_tasks.run_analysis_task": {"queue": "analysis"},
        "app.workers.periodic_tasks.update_all_raster_layers": {"queue": "periodic"},
        "app.workers.periodic_tasks.generate_alerts_for_anomalies": {"queue": "periodic"},
    },
    # Beat schedule para tareas periódicas
    beat_schedule={
        "update-raster-layers-daily": {
            "task": "app.workers.periodic_tasks.update_all_raster_layers",
            "schedule": crontab(hour=2, minute=0),  # 2:00 AM diario
        },
        "generate-alerts-daily": {
            "task": "app.workers.periodic_tasks.generate_alerts_for_anomalies",
            "schedule": crontab(hour=3, minute=0),  # 3:00 AM diario
        },
    },
)

# Configuración de result backend
celery_app.conf.result_expires = 86400  # 24 horas
celery_app.conf.result_compression = "gzip"