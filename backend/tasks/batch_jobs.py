"""Background batch jobs for attendance and notifications.

This module provides scheduled jobs for:
1. Auto-attendance: Mark unattended sessions as ATTENDED at 23:59 daily
2. Attendance reminder: Remind tutors to check attendance at 12:00 daily
3. Session reminder: Send 24-hour-before session reminders to students

Jobs can be scheduled using Celery Beat, APScheduler, or any cron-compatible scheduler.
"""
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from domain.entities import SessionStatus, BookingStatus
from infrastructure.database import get_async_session
from infrastructure.external.kakao_alimtalk import KakaoAlimtalkAdapter
from infrastructure.persistence.repositories.attendance_repository import AttendanceRepository
from infrastructure.persistence.repositories.booking_repository import BookingRepository


class BatchJobResult:
    """Result of a batch job execution."""
    def __init__(
        self,
        success: bool,
        processed_count: int = 0,
        failed_count: int = 0,
        errors: list[str] | None = None,
        message: str = "",
    ):
        self.success = success
        self.processed_count = processed_count
        self.failed_count = failed_count
        self.errors = errors or []
        self.message = message

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "errors": self.errors,
            "message": self.message,
        }


async def auto_attendance_job(target_date: Optional[date] = None) -> BatchJobResult:
    """
    Auto-attendance job: Mark unattended sessions as ATTENDED.

    Runs daily at 23:59 (configurable via BATCH_AUTO_ATTENDANCE_SCHEDULE).

    Logic:
    - Find all SCHEDULED sessions on or before target_date
    - Mark them as COMPLETED (auto-attendance)
    - Update booking's completed_sessions count

    Args:
        target_date: Date to check sessions for (defaults to yesterday)

    Returns:
        BatchJobResult with processing statistics
    """
    if not settings.BATCH_JOBS_ENABLED:
        return BatchJobResult(success=True, message="Batch jobs disabled")

    if target_date is None:
        # Default to yesterday (run at 23:59 means we're processing today's sessions)
        target_date = date.today()

    processed = 0
    failed = 0
    errors = []

    try:
        async for db in get_async_session():
            attendance_repo = AttendanceRepository(db)

            # Get sessions needing auto-attendance
            sessions = await attendance_repo.get_sessions_needing_attendance(target_date)

            for session in sessions:
                try:
                    # Mark session as completed (auto-attendance)
                    await attendance_repo.update_session_status(
                        session_id=session.id,
                        status=SessionStatus.COMPLETED,
                    )
                    processed += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"Session {session.id}: {str(e)}")

            await db.commit()

            message = (
                f"Auto-attendance completed for {target_date}. "
                f"Processed: {processed}, Failed: {failed}"
            )
            return BatchJobResult(
                success=True,
                processed_count=processed,
                failed_count=failed,
                errors=errors,
                message=message,
            )

    except Exception as e:
        return BatchJobResult(
            success=False,
            errors=[f"Job failed: {str(e)}"],
            message=f"Auto-attendance job failed: {str(e)}",
        )


async def attendance_reminder_job(target_date: Optional[date] = None) -> BatchJobResult:
    """
    Attendance check reminder job: Remind tutors to mark attendance.

    Runs daily at 12:00 (configurable via BATCH_ATTENDANCE_REMINDER_SCHEDULE).

    Logic:
    - Find tutors with unattended sessions from previous day
    - Send Alimtalk reminder to each tutor

    Args:
        target_date: Date to check for unattended sessions (defaults to yesterday)

    Returns:
        BatchJobResult with processing statistics
    """
    if not settings.BATCH_JOBS_ENABLED:
        return BatchJobResult(success=True, message="Batch jobs disabled")

    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    processed = 0
    failed = 0
    errors = []

    try:
        async for db in get_async_session():
            attendance_repo = AttendanceRepository(db)
            alimtalk_adapter = KakaoAlimtalkAdapter()

            # Get tutors who need attendance reminder
            tutors = await attendance_repo.get_tutors_for_attendance_reminder(target_date)

            for tutor_data in tutors:
                try:
                    template_code = settings.KAKAO_ALIMTalk_TEMPLATE_ATTENDANCE_CHECK
                    if not template_code:
                        errors.append(f"No template code configured for attendance reminder")
                        continue

                    # Send Alimtalk reminder
                    variables = {
                        "tutor_name": tutor_data["tutor_name"],
                        "date": target_date.strftime("%Y-%m-%d"),
                        "unattended_count": str(tutor_data["unattended_count"]),
                        "content": (
                            f"{tutor_data['tutor_name']} 선생님, "
                            f"{target_date.strftime('%m월 %d일')} "
                            f"출석 체크되지 않은 수업이 {tutor_data['unattended_count']}건 있습니다. "
                            f"지금 확인해주세요."
                        ),
                    }

                    await alimtalk_adapter.send_alimtalk(
                        phone=tutor_data["tutor_phone"],
                        template_code=template_code,
                        variables=variables,
                    )
                    processed += 1

                except Exception as e:
                    failed += 1
                    errors.append(f"Tutor {tutor_data['tutor_id']}: {str(e)}")

            message = (
                f"Attendance reminder completed for {target_date}. "
                f"Processed: {processed}, Failed: {failed}"
            )
            return BatchJobResult(
                success=True,
                processed_count=processed,
                failed_count=failed,
                errors=errors,
                message=message,
            )

    except Exception as e:
        return BatchJobResult(
            success=False,
            errors=[f"Job failed: {str(e)}"],
            message=f"Attendance reminder job failed: {str(e)}",
        )


async def session_reminder_job(target_date: Optional[date] = None) -> BatchJobResult:
    """
    Session reminder job: Send 24-hour-before reminders to students.

    Runs daily at 09:00 (configurable via BATCH_SESSION_REMINDER_SCHEDULE).

    Logic:
    - Find all sessions scheduled for tomorrow
    - Send reminder to students with session details

    Args:
        target_date: Date of sessions to remind about (defaults to tomorrow)

    Returns:
        BatchJobResult with processing statistics
    """
    if not settings.BATCH_JOBS_ENABLED:
        return BatchJobResult(success=True, message="Batch jobs disabled")

    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    processed = 0
    failed = 0
    errors = []

    try:
        async for db in get_async_session():
            attendance_repo = AttendanceRepository(db)
            alimtalk_adapter = KakaoAlimtalkAdapter()

            # Get upcoming sessions
            sessions = await attendance_repo.get_upcoming_sessions_for_reminder(target_date)

            for session_data in sessions:
                try:
                    template_code = settings.KAKAO_ALIMTalk_TEMPLATE_SESSION_REMINDER
                    if not template_code:
                        errors.append(f"No template code configured for session reminder")
                        continue

                    session = session_data["session"]
                    student_name = session_data["student_name"]
                    parent_phone = session_data["parent_phone"]

                    # Format session time
                    session_datetime = session.session_date.strftime("%Y-%m-%d") + " " + session.session_time

                    # Send Alimtalk reminder to parent
                    variables = {
                        "student_name": student_name,
                        "session_date": session.session_date.strftime("%Y년 %m월 %d일"),
                        "session_time": session.session_time,
                        "tutor_name": session_data["tutor_name"],
                        "content": (
                            f"{student_name} 학생의 내일 수업이 예정되어 있습니다. "
                            f"일시: {session.session_date.strftime('%m월 %d일')} {session.session_time} "
                            f"선생님: {session_data['tutor_name']}"
                        ),
                    }

                    await alimtalk_adapter.send_alimtalk(
                        phone=parent_phone,
                        template_code=template_code,
                        variables=variables,
                    )
                    processed += 1

                except Exception as e:
                    failed += 1
                    errors.append(f"Session {session.id if session else 'unknown'}: {str(e)}")

            message = (
                f"Session reminder completed for {target_date}. "
                f"Processed: {processed}, Failed: {failed}"
            )
            return BatchJobResult(
                success=True,
                processed_count=processed,
                failed_count=failed,
                errors=errors,
                message=message,
            )

    except Exception as e:
        return BatchJobResult(
            success=False,
            errors=[f"Job failed: {str(e)}"],
            message=f"Session reminder job failed: {str(e)}",
        )


async def run_all_jobs(target_date: Optional[date] = None) -> dict[str, BatchJobResult]:
    """
    Run all batch jobs and return results.

    Useful for testing or manual execution.

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


# Celery Beat integration example (if using Celery)
# This shows how to integrate with Celery Beat scheduler
# Install: pip install celery
# Run: celery -A infrastructure.celery_app beat --loglevel=info

try:
    from celery import Celery
    from celery.schedules import crontab

    # Create Celery app (optional - only if using Celery)
    celery_app = Celery(
        "tutorflow",
        broker=settings.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=settings.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
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
            "task": "tasks.batch_jobs.celery_auto_attendance_task",
            "schedule": crontab(hour=23, minute=59),  # 23:59 daily
        },
        "attendance-reminder-daily": {
            "task": "tasks.batch_jobs.celery_attendance_reminder_task",
            "schedule": crontab(hour=12, minute=0),  # 12:00 daily
        },
        "session-reminder-daily": {
            "task": "tasks.batch_jobs.celery_session_reminder_task",
            "schedule": crontab(hour=9, minute=0),  # 09:00 daily
        },
    }

    CELERY_AVAILABLE = True

except ImportError:
    # Celery not installed, tasks can still be run manually or with other schedulers
    CELERY_AVAILABLE = False
    celery_app = None
