import os
from celery import Celery
from dotenv import load_dotenv
from concurrency import calculate_queue_concurrency

load_dotenv()

celery_app = Celery(
    "munka",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    include=["celery_tasks"],
)
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600
celery_app.conf.worker_concurrency = calculate_queue_concurrency()
celery_app.conf.task_routes = {
    "tasks.analisar_commit": {"queue": "analises"},
    "tasks.enviar_atividade": {"queue": "envios"},
    "tasks.verificar_lancamento": {"queue": "envios"},
    "tasks.corrigir_lancamento": {"queue": "envios"},
}

