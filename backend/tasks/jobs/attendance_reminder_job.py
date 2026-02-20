"""Attendance reminder batch job.

Remind tutors to check attendance at 12:00 daily.
"""
from datetime import date, timedelta
from typing import Optional

from config import settings
from infrastructure.database import get_async_session
from infrastructure.external.kakao_alimtalk import KakaoAlimtalkAdapter
from infrastructure.persistence.repositories.attendance_repository import AttendanceRepository
from tasks.jobs.base import BatchJobResult


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
                        errors.append("No template code configured for attendance reminder")
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
