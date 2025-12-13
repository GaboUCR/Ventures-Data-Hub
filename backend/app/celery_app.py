# app/celery_app.py
from __future__ import annotations

import os
from gevent import monkey

monkey.patch_all()

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ace_portfolio_intelligence",
    broker=REDIS_URL,
    backend=REDIS_URL,  # optional
    # Explicitly include task modules so Celery always imports them
    include=[
        "app.etl.celery_tasks_stripe",
        "app.etl.celery_tasks_ga4",
    ],
)

# Minimal config; you can move these into settings later
celery_app.conf.update(
    task_default_queue="default",
    task_routes={
        "etl.*": {"queue": "etl"},
    },
)

# Periodic schedule (Celery beat)
celery_app.conf.beat_schedule = {
    "stripe-etl-every-2-minutes": {
        "task": "etl.stripe.sync_all_companies",
        "schedule": 120,  # seconds
        "args": (2,),       # days window
    },
    "ga4-etl-every-2-minutes": {
        "task": "etl.ga4.sync_all_companies",
        "schedule": 120.0,
        "args": (2,),
    },
}
