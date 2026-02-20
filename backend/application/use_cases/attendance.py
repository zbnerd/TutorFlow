"""Attendance use cases for managing session attendance."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from domain.entities import (
    Booking,
    BookingSession,
    Attendance,
    AttendanceStatus,
    NoShowPolicy,
)
from domain.value_objects.no_show_policy import (
    NoShowPolicyConfig,
    get_policy_by_type,
)
from domain.ports import BookingRepositoryPort


class AttendanceValidationError(Exception):
    """Raised when attendance validation fails."""

    def __init__(self, message: str, code: str = "ATTENDANCE_VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass
class AttendanceUseCases:
    """Attendance management use cases."""

    booking_repo: BookingRepositoryPort

    async def mark_attendance(
        self,
        session_id: int,
        status: AttendanceStatus,
        checked_by_id: int,
        notes: Optional[str] = None,
    ) -> BookingSession:
        """
        Mark attendance for a booking session.

        This updates the session status and optionally increments
        the booking's completed_sessions counter.

        Args:
            session_id: Booking session ID
            status: Attendance status (ATTENDED, NO_SHOW, CANCELLED)
            checked_by_id: User ID of the person marking attendance
            notes: Optional notes about the attendance

        Returns:
            Updated booking session entity

        Raises:
            AttendanceValidationError: If validation fails
        """
        session = await self.booking_repo.find_session_by_id(session_id)
        if not session:
            raise AttendanceValidationError("Session not found", "SESSION_NOT_FOUND")

        booking = await self.booking_repo.find_by_id(session.booking_id)
        if not booking:
            raise AttendanceValidationError("Booking not found", "BOOKING_NOT_FOUND")

        # Validate session is in schedulable state
        if session.status not in [
            AttendanceStatus.ATTENDED,
            AttendanceStatus.NO_SHOW,
            AttendanceStatus.CANCELLED,
        ]:
            # Using ORM SessionStatus values: SCHEDULED, COMPLETED, CANCELLED, NO_SHOW
            from infrastructure.persistence.models.booking_model import SessionStatus
            if session.status not in [SessionStatus.SCHEDULED]:
                raise AttendanceValidationError(
                    f"Cannot mark attendance for session with status {session.status.value}",
                    "INVALID_SESSION_STATUS",
                )

        # Update session status
        from infrastructure.persistence.models.booking_model import SessionStatus

        if status == AttendanceStatus.ATTENDED:
            session.status = SessionStatus.COMPLETED
            # Increment completed sessions count
            if booking.completed_sessions is None:
                booking.completed_sessions = 0
            booking.completed_sessions += 1
        elif status == AttendanceStatus.NO_SHOW:
            session.status = SessionStatus.NO_SHOW
        elif status == AttendanceStatus.CANCELLED:
            session.status = SessionStatus.CANCELLED

        session.attendance_checked_at = datetime.utcnow()
        session.attendance_checked_by = checked_by_id
        session.notes = notes

        # Save session
        await self.booking_repo.update_session(session)
        await self.booking_repo.save(booking)

        # Update booking status if all sessions are completed
        if booking.completed_sessions >= booking.total_sessions:
            booking.status = "COMPLETED"
            await self.booking_repo.save(booking)

        return session

    async def handle_no_show(
        self,
        session_id: int,
        checked_by_id: int,
        notes: Optional[str] = None,
    ) -> tuple[BookingSession, bool]:
        """
        Handle a no-show according to the tutor's no-show policy.

        This marks the session as NO_SHOW and determines if it should be billed
        based on the tutor's policy and monthly no-show count.

        Args:
            session_id: Booking session ID
            checked_by_id: User ID of the person marking no-show
            notes: Optional notes about the no-show

        Returns:
            Tuple of (updated session, is_billable)

        Raises:
            AttendanceValidationError: If validation fails
        """
        session = await self.booking_repo.find_session_by_id(session_id)
        if not session:
            raise AttendanceValidationError("Session not found", "SESSION_NOT_FOUND")

        booking = await self.booking_repo.find_by_id(session.booking_id)
        if not booking:
            raise AttendanceValidationError("Booking not found", "BOOKING_NOT_FOUND")

        # Get tutor's no-show policy
        tutor = await self.booking_repo.find_tutor_by_id(booking.tutor_id)
        if not tutor:
            raise AttendanceValidationError("Tutor not found", "TUTOR_NOT_FOUND")

        # Get monthly no-show count for this student-tutor pair
        year_month = datetime.now().strftime("%Y-%m")
        no_show_count = await self.booking_repo.count_no_shows_in_month(
            booking.tutor_id,
            booking.student_id,
            year_month,
        )

        # Determine if billable based on policy
        policy_config = get_policy_by_type(tutor.no_show_policy.value)
        is_first_of_month = no_show_count == 0
        is_billable = policy_config.is_billable_on_no_show(
            no_show_count + 1,  # Include current no-show
            is_first_of_month,
        )

        # Mark session as NO_SHOW
        session = await self.mark_attendance(
            session_id,
            AttendanceStatus.NO_SHOW,
            checked_by_id,
            notes,
        )

        return session, is_billable

    async def get_attendance_records(
        self,
        booking_id: int,
        requesting_user_id: int,
    ) -> List[BookingSession]:
        """
        Get attendance records for a booking.

        Args:
            booking_id: Booking ID
            requesting_user_id: User ID requesting the records (for authorization)

        Returns:
            List of booking sessions with attendance info

        Raises:
            AttendanceValidationError: If not authorized
        """
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            raise AttendanceValidationError("Booking not found", "BOOKING_NOT_FOUND")

        # Check authorization: must be tutor or student of this booking
        if booking.tutor_id != requesting_user_id and booking.student_id != requesting_user_id:
            raise AttendanceValidationError("Not authorized to view these records", "NOT_AUTHORIZED")

        sessions = await self.booking_repo.list_sessions(booking_id)
        return sessions

    async def get_no_show_stats(
        self,
        tutor_id: int,
        student_id: int,
        year_month: str,
    ) -> dict:
        """
        Get no-show statistics for a student-tutor pair in a given month.

        Args:
            tutor_id: Tutor ID
            student_id: Student ID
            year_month: Year-month string (e.g., "2024-01")

        Returns:
            Dictionary with no-show statistics

        Raises:
            AttendanceValidationError: If validation fails
        """
        # Validate year_month format
        try:
            datetime.strptime(year_month, "%Y-%m")
        except ValueError:
            raise AttendanceValidationError(
                "Invalid year_month format. Expected 'YYYY-MM'",
                "INVALID_DATE_FORMAT",
            )

        # Get sessions for this month
        sessions = await self.booking_repo.list_sessions_by_month(
            tutor_id,
            student_id,
            year_month,
        )

        # Calculate statistics
        total_sessions = len(sessions)
        attended_sessions = sum(
            1 for s in sessions if s.status == "COMPLETED"
        )
        no_show_count = sum(
            1 for s in sessions if s.status == "NO_SHOW"
        )

        # Get tutor's policy to determine if free no-show has been used
        tutor = await self.booking_repo.find_tutor_by_id(tutor_id)
        if not tutor:
            raise AttendanceValidationError("Tutor not found", "TUTOR_NOT_FOUND")

        policy_config = get_policy_by_type(tutor.no_show_policy.value)
        free_allowance = policy_config.get_free_no_show_allowance()
        free_no_show_used = (
            free_allowance == 1 and no_show_count > 0
        ) if free_allowance > 0 else False

        return {
            "tutor_id": tutor_id,
            "student_id": student_id,
            "year_month": year_month,
            "total_sessions": total_sessions,
            "attended_sessions": attended_sessions,
            "no_show_count": no_show_count,
            "free_no_show_used": free_no_show_used,
        }

    async def auto_mark_attendance_deadline(self) -> List[BookingSession]:
        """
        Batch job: Auto-mark attendance for sessions past the deadline.

        Attendance deadline is next day 23:59 after the scheduled session time.
        Sessions not marked by then are automatically marked as ATTENDED.

        Returns:
            List of sessions that were auto-marked
        """
        # Find all scheduled sessions past the deadline without attendance
        sessions = await self.booking_repo.find_sessions_past_deadline()

        auto_marked = []
        for session in sessions:
            # Auto-mark as attended (lenient policy)
            marked = await self.mark_attendance(
                session.id,
                AttendanceStatus.ATTENDED,
                None,  # System check
                "Auto-marked: Attendance deadline passed",
            )
            auto_marked.append(marked)

        return auto_marked
