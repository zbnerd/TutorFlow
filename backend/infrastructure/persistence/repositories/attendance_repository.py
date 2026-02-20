"""Attendance repository implementation."""
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities import BookingSession, Booking, SessionStatus, BookingStatus
from infrastructure.persistence.models import BookingSessionModel, BookingModel, TutorModel, StudentModel, UserModel
from infrastructure.persistence.repositories.audit_log_repository import AuditLogRepository


class AttendanceRepository:
    """Repository for attendance-related operations."""

    def __init__(self, session: AsyncSession, audit_repo: Optional[AuditLogRepository] = None):
        """Initialize repository with database session and optional audit repository."""
        self.session = session
        self.audit_repo = audit_repo

    async def get_session_by_id(self, session_id: int) -> Optional[BookingSession]:
        """Get a booking session by ID."""
        result = await self.session.execute(
            select(BookingSessionModel).where(BookingSessionModel.id == session_id)
        )
        db_session = result.scalar_one_or_none()
        return self._session_to_entity(db_session) if db_session else None

    async def get_sessions_for_tutor(
        self,
        tutor_id: int,
        status_filter: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[dict]:
        """Get sessions for a tutor that need attendance check.

        Returns sessions with booking and student information.
        """
        query = (
            select(BookingSessionModel, BookingModel, StudentModel, UserModel)
            .join(BookingModel, BookingSessionModel.booking_id == BookingModel.id)
            .join(StudentModel, BookingModel.student_id == StudentModel.id)
            .join(UserModel, StudentModel.user_id == UserModel.id)
            .where(BookingModel.tutor_id == tutor_id)
        )

        if status_filter:
            query = query.where(BookingSessionModel.status == status_filter)

        if date_from:
            query = query.where(BookingSessionModel.session_date >= date_from)

        if date_to:
            query = query.where(BookingSessionModel.session_date <= date_to)

        query = query.order_by(BookingSessionModel.session_date.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        rows = result.all()

        sessions = []
        for db_session, db_booking, db_student, db_user in rows:
            sessions.append({
                "session": self._session_to_entity(db_session),
                "booking": {
                    "id": db_booking.id,
                    "student_id": db_booking.student_id,
                    "tutor_id": db_booking.tutor_id,
                    "status": db_booking.status,
                },
                "student": {
                    "id": db_student.id,
                    "name": db_user.name,
                    "grade": db_student.grade,
                },
            })

        return sessions

    async def get_sessions_needing_attendance(self, day: date) -> List[BookingSession]:
        """Get all sessions that need attendance check for a specific day.

        Sessions that need attendance are:
        - Status is SCHEDULED
        - Session date is the given day or before
        - Not yet attendance checked
        """
        result = await self.session.execute(
            select(BookingSessionModel)
            .join(BookingModel, BookingSessionModel.booking_id == BookingModel.id)
            .where(
                and_(
                    BookingSessionModel.status == SessionStatus.SCHEDULED,
                    BookingSessionModel.session_date <= day,
                    BookingModel.status.in_([
                        BookingStatus.APPROVED,
                        BookingStatus.IN_PROGRESS,
                    ]),
                )
            )
            .order_by(BookingSessionModel.session_date.asc())
        )
        db_sessions = result.scalars().all()
        return [self._session_to_entity(s) for s in db_sessions]

    async def get_upcoming_sessions_for_reminder(self, target_date: date) -> List[dict]:
        """Get sessions scheduled for target_date (for 24-hour reminder).

        Returns sessions with student and tutor contact information.
        """
        result = await self.session.execute(
            select(BookingSessionModel, BookingModel, StudentModel, UserModel)
            .join(BookingModel, BookingSessionModel.booking_id == BookingModel.id)
            .join(StudentModel, BookingModel.student_id == StudentModel.id)
            .join(UserModel, StudentModel.user_id == UserModel.id)
            .join(TutorModel, BookingModel.tutor_id == TutorModel.id)
            .where(
                and_(
                    BookingSessionModel.session_date == target_date,
                    BookingSessionModel.status == SessionStatus.SCHEDULED,
                    BookingModel.status.in_([
                        BookingStatus.APPROVED,
                        BookingStatus.IN_PROGRESS,
                    ]),
                )
            )
            .order_by(BookingSessionModel.session_time.asc())
        )
        rows = result.all()

        sessions = []
        for db_session, db_booking, db_student, db_user in rows:
            # Get tutor user info
            tutor_result = await self.session.execute(
                select(UserModel).join(TutorModel, UserModel.id == TutorModel.user_id)
                .where(TutorModel.id == db_booking.tutor_id)
            )
            tutor_user = tutor_result.scalar_one_or_none()

            sessions.append({
                "session": self._session_to_entity(db_session),
                "booking_id": db_booking.id,
                "student_name": db_user.name,
                "student_phone": db_student.parent_phone,
                "tutor_name": tutor_user.name if tutor_user else None,
                "tutor_phone": tutor_user.phone if tutor_user else None,
                "session_date": db_session.session_date,
                "session_time": db_session.session_time,
            })

        return sessions

    async def get_tutors_for_attendance_reminder(self, target_date: date) -> List[dict]:
        """Get tutors who have unattended sessions from target_date.

        For sending attendance check reminders at 12:00 the next day.
        """
        result = await self.session.execute(
            select(TutorModel, UserModel, func.count(BookingSessionModel.id).label("unattended_count"))
            .join(BookingModel, TutorModel.id == BookingModel.tutor_id)
            .join(BookingSessionModel, BookingModel.id == BookingSessionModel.booking_id)
            .join(UserModel, TutorModel.user_id == UserModel.id)
            .where(
                and_(
                    BookingSessionModel.session_date == target_date,
                    BookingSessionModel.status == SessionStatus.SCHEDULED,
                    BookingSessionModel.attendance_checked_at.is_(None),
                    BookingModel.status.in_([
                        BookingStatus.APPROVED,
                        BookingStatus.IN_PROGRESS,
                    ]),
                )
            )
            .group_by(TutorModel.id, UserModel.id)
        )

        tutors = []
        for db_tutor, db_user, unattended_count in result:
            tutors.append({
                "tutor_id": db_tutor.id,
                "tutor_name": db_user.name,
                "tutor_phone": db_user.phone,
                "unattended_count": unattended_count,
                "date": target_date,
            })

        return tutors

    async def update_session_attendance(
        self,
        session_id: int,
        status: SessionStatus,
        checked_by: int,
        ip_address: Optional[str] = None,
    ) -> Optional[BookingSession]:
        """Update session attendance status."""
        result = await self.session.execute(
            select(BookingSessionModel).where(BookingSessionModel.id == session_id)
        )
        db_session = result.scalar_one_or_none()

        if not db_session:
            return None

        old_status = db_session.status
        db_session.status = status
        db_session.attendance_checked_at = datetime.utcnow()
        db_session.attendance_checked_by = checked_by

        await self.session.flush()
        await self.session.refresh(db_session)

        # Log attendance change
        if self.audit_repo and old_status != status:
            await self.audit_repo.log_change(
                entity_type="booking_session",
                entity_id=session_id,
                action="attendance_check",
                old_value={"status": old_status.value if isinstance(old_status, SessionStatus) else old_status},
                new_value={"status": status.value if isinstance(status, SessionStatus) else status},
                actor_id=checked_by,
                ip_address=ip_address,
            )

        # Update booking completed_sessions count if marking as completed
        if status == SessionStatus.COMPLETED and old_status != SessionStatus.COMPLETED:
            await self._increment_completed_sessions(db_session.booking_id, checked_by, ip_address)

        return self._session_to_entity(db_session)

    async def update_session_status(
        self,
        session_id: int,
        status: SessionStatus,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[BookingSession]:
        """Update session status (for batch job auto-attendance)."""
        result = await self.session.execute(
            select(BookingSessionModel).where(BookingSessionModel.id == session_id)
        )
        db_session = result.scalar_one_or_none()

        if not db_session:
            return None

        old_status = db_session.status
        db_session.status = status
        db_session.attendance_checked_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(db_session)

        # Log status change
        if self.audit_repo and old_status != status:
            await self.audit_repo.log_change(
                entity_type="booking_session",
                entity_id=session_id,
                action="auto_attendance",
                old_value={"status": old_status.value if isinstance(old_status, SessionStatus) else old_status},
                new_value={"status": status.value if isinstance(status, SessionStatus) else status},
                actor_id=actor_id,  # System user ID for batch jobs
                ip_address=ip_address,
            )

        # Update booking completed_sessions count if marking as completed
        if status == SessionStatus.COMPLETED and old_status != SessionStatus.COMPLETED:
            await self._increment_completed_sessions(db_session.booking_id, actor_id, ip_address)

        return self._session_to_entity(db_session)

    async def _increment_completed_sessions(
        self,
        booking_id: int,
        actor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Increment the completed_sessions count for a booking."""
        result = await self.session.execute(
            select(BookingModel).where(BookingModel.id == booking_id)
        )
        db_booking = result.scalar_one_or_none()

        if db_booking:
            old_count = db_booking.completed_sessions
            db_booking.completed_sessions += 1
            await self.session.flush()

            # Log the increment
            if self.audit_repo:
                await self.audit_repo.log_change(
                    entity_type="booking",
                    entity_id=booking_id,
                    action="increment_completed_sessions",
                    old_value={"completed_sessions": old_count},
                    new_value={"completed_sessions": db_booking.completed_sessions},
                    actor_id=actor_id,
                    ip_address=ip_address,
                )

    async def get_attendance_status(
        self,
        user_id: int,
        is_tutor: bool,
        offset: int = 0,
        limit: int = 20,
    ) -> dict:
        """Get attendance status summary for a user.

        Returns counts of sessions by status and recent sessions.
        """
        if is_tutor:
            # Get tutor_id from user_id
            result = await self.session.execute(
                select(TutorModel).where(TutorModel.user_id == user_id)
            )
            tutor = result.scalar_one_or_none()
            if not tutor:
                return {"total": 0, "by_status": {}, "recent_sessions": []}

            # Get bookings for this tutor
            bookings_result = await self.session.execute(
                select(BookingModel.id).where(BookingModel.tutor_id == tutor.id)
            )
            booking_ids = [row[0] for row in bookings_result]
        else:
            # Get student_id from user_id
            result = await self.session.execute(
                select(StudentModel).where(StudentModel.user_id == user_id)
            )
            student = result.scalar_one_or_none()
            if not student:
                return {"total": 0, "by_status": {}, "recent_sessions": []}

            # Get bookings for this student
            bookings_result = await self.session.execute(
                select(BookingModel.id).where(BookingModel.student_id == student.id)
            )
            booking_ids = [row[0] for row in bookings_result]

        if not booking_ids:
            return {"total": 0, "by_status": {}, "recent_sessions": []}

        # Get status counts
        stats_result = await self.session.execute(
            select(
                BookingSessionModel.status,
                func.count(BookingSessionModel.id).label("count")
            )
            .where(BookingSessionModel.booking_id.in_(booking_ids))
            .group_by(BookingSessionModel.status)
        )

        by_status = {status.value: count for status, count in stats_result.all()}
        total = sum(by_status.values())

        # Get recent sessions
        recent_result = await self.session.execute(
            select(BookingSessionModel)
            .where(BookingSessionModel.booking_id.in_(booking_ids))
            .order_by(BookingSessionModel.session_date.desc())
            .offset(offset)
            .limit(limit)
        )
        recent_sessions = [
            self._session_to_entity(s) for s in recent_result.scalars().all()
        ]

        return {
            "total": total,
            "by_status": by_status,
            "recent_sessions": recent_sessions,
        }

    def _session_to_entity(self, db_session: BookingSessionModel) -> BookingSession:
        """Convert ORM model to domain entity."""
        return BookingSession(
            id=db_session.id,
            booking_id=db_session.booking_id,
            session_date=db_session.session_date,
            session_time=db_session.session_time,
            status=db_session.status,
            attendance_checked_at=db_session.attendance_checked_at,
            attendance_checked_by=db_session.attendance_checked_by,
            notes=db_session.notes,
        )
