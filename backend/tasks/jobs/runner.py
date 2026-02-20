"""Utility to run all batch jobs.

Useful for testing or manual execution.
"""
from datetime import date, timedelta
from typing import Optional

from tasks.jobs.auto_attendance_job import auto_attendance_job
from tasks.jobs.attendance_reminder_job import attendance_reminder_job
from tasks.jobs.session_reminder_job import session_reminder_job


async def run_all_jobs(target_date: Optional[date] = None) -> dict:
    """
    Run all batch jobs and return results.

    Args:
        target_date: Date to run jobs for (defaults to appropriate date for each job)

    Returns:
        Dictionary mapping job names to their results
    """
    results = {}

    # Auto-attendance runs on today's date
    results["auto_attendance"] = await auto_attendance_job(target_date or date.today())

    # Attendance reminder checks yesterday's sessions
    reminder_date = target_date or (date.today() - timedelta(days=1))
    results["attendance_reminder"] = await attendance_reminder_job(reminder_date)

    # Session reminder reminds for tomorrow's sessions
    session_date = target_date or (date.today() + timedelta(days=1))
    results["session_reminder"] = await session_reminder_job(session_date)

    return results
