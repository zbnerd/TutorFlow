"""Auto-attendance batch job.

Mark unattended sessions as ATTENDED at 23:59 daily.
"""
from datetime import date
from typing import Optional

from config import settings
from domain.entities import SessionStatus
from infrastructure.database import get_async_session
from infrastructure.persistence.repositories.attendance_repository import AttendanceRepository
from tasks.jobs.base import BatchJobResult


async def auto_attendance_job(target_date: Optional[date] = None) -> BatchJobResult:
    """
    Auto-attendance job: Mark unattended sessions as ATTENDED.

    Runs daily at 23:59 (configurable via BATCH_AUTO_ATTENDANCE_SCHEDULE).

    Logic:
    - Find all SCHEDULED sessions on or before target_date
    - Mark them as COMPLETED (auto-attendance)
    - Update booking's completed_sessions count

    Args:
        target_date: Date to check sessions for (defaults to today)

    Returns:
        BatchJobResult with processing statistics
    """
    if not settings.BATCH_JOBS_ENABLED:
        return BatchJobResult(success=True, message="Batch jobs disabled")

    if target_date is None:
        # Default to today (run at 23:59 means we're processing today's sessions)
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
