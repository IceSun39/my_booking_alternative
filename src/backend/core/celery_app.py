from celery import Celery
from .celery_config import settings

celery = Celery(
    "backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.backend.tasks.email_tasks"]
)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    timezone=settings.CELERY_TIMEZONE,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)