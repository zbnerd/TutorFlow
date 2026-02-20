"""Session reminder batch job.

Send 24-hour-before session reminders to students.
"""
from datetime import date, timedelta
from typing import Optional

from config import settings
from infrastructure.database import get_async_session
from infrastructure.external.kakao_alimtalk import KakaoAlimtalkAdapter
from infrastructure.persistence.repositories.attendance_repository import AttendanceRepository
from tasks.jobs.base import BatchJobResult


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
                        errors.append("No template code configured for session reminder")
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
