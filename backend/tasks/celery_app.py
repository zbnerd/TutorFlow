"""Celery configuration and task definitions.

This module provides Celery Beat integration for batch job scheduling.
Install: pip install celery
Run: celery -A tasks.celery_app beat --loglevel=info
"""
import asyncio
from datetime import date
from typing import Optional

from celery import Celery
from celery.schedules import crontab

from config import settings
from tasks.jobs.auto_attendance_job import auto_attendance_job
from tasks.jobs.attendance_reminder_job import attendance_reminder_job
from tasks.jobs.session_reminder_job import session_reminder_job

# Create Celery app
celery_app = Celery(
    "tutorflow",
    broker=getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=getattr(settings, "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)


@celery_app.task
def celery_auto_attendance_task(target_date_str: Optional[str] = None):
    """Celery task wrapper for auto-attendance job."""
    target_date = date.fromisoformat(target_date_str) if target_date_str else None
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(auto_attendance_job(target_date))
    return result.to_dict()


@celery_app.task
def celery_attendance_reminder_task(target_date_str: Optional[str] = None):
    """Celery task wrapper for attendance reminder job."""
    target_date = date.fromisoformat(target_date_str) if target_date_str else None
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(attendance_reminder_job(target_date))
    return result.to_dict()


@celery_app.task
def celery_session_reminder_task(target_date_str: Optional[str] = None):
    """Celery task wrapper for session reminder job."""
    target_date = date.fromisoformat(target_date_str) if target_date_str else None
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(session_reminder_job(target_date))
    return result.to_dict()


# Celery Beat schedule configuration
celery_app.conf.beat_schedule = {
    "auto-attendance-daily": {
        "task": "tasks.celery_app.celery_auto_attendance_task",
        "schedule": crontab(hour=23, minute=59),  # 23:59 daily
    },
    "attendance-reminder-daily": {
        "task": "tasks.celery_app.celery_attendance_reminder_task",
        "schedule": crontab(hour=12, minute=0),  # 12:00 daily
    },
    "session-reminder-daily": {
        "task": "tasks.celery_app.celery_session_reminder_task",
        "schedule": crontab(hour=9, minute=0),  # 09:00 daily
    },
}
