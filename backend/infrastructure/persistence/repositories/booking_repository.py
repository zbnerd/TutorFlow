"""Booking repository implementation."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities import Booking, BookingSession, BookingStatus, SessionStatus
from domain.ports import BookingRepositoryPort
from domain.value_objects.schedule import ScheduleSlot, TimeRange
from infrastructure.persistence.models import BookingModel, BookingSessionModel


class BookingRepository(BookingRepositoryPort):
    """SQLAlchemy implementation of BookingRepositoryPort."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def save(self, booking: Booking) -> Booking:
        """Save booking to database (create or update)."""
        if booking.id is None:
            # Create new booking
            db_booking = BookingModel(
                student_id=booking.student_id,
                tutor_id=booking.tutor_id,
                total_sessions=booking.total_sessions,
                completed_sessions=booking.completed_sessions,
                status=booking.status,
                notes=booking.notes,
            )
            self.session.add(db_booking)
            await self.session.flush()
            await self.session.refresh(db_booking)
            return self._to_entity(db_booking)
        else:
            # Update existing booking
            result = await self.session.execute(
                select(BookingModel).where(BookingModel.id == booking.id)
            )
            db_booking = result.scalar_one_or_none()
            if db_booking:
                db_booking.status = booking.status
                db_booking.completed_sessions = booking.completed_sessions
                db_booking.notes = booking.notes
                await self.session.flush()
                await self.session.refresh(db_booking)
                return self._to_entity(db_booking)
            return booking

    async def find_by_id(self, booking_id: int) -> Optional[Booking]:
        """Find booking by ID."""
        result = await self.session.execute(
            select(BookingModel)
            .options(selectinload(BookingModel.sessions))
            .where(BookingModel.id == booking_id)
        )
        db_booking = result.scalar_one_or_none()
        return self._to_entity(db_booking) if db_booking else None

    async def list_by_tutor(
        self,
        tutor_id: int,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Booking]:
        """List bookings by tutor."""
        query = select(BookingModel).where(BookingModel.tutor_id == tutor_id)
        if status:
            query = query.where(BookingModel.status == status)
        query = query.order_by(BookingModel.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_bookings = result.scalars().all()
        return [self._to_entity(b) for b in db_bookings]

    async def list_by_student(
        self,
        student_id: int,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Booking]:
        """List bookings by student."""
        query = select(BookingModel).where(BookingModel.student_id == student_id)
        if status:
            query = query.where(BookingModel.status == status)
        query = query.order_by(BookingModel.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        db_bookings = result.scalars().all()
        return [self._to_entity(b) for b in db_bookings]

    async def find_conflicting_slots(
        self,
        tutor_id: int,
        slots: List[ScheduleSlot],
    ) -> List[ScheduleSlot]:
        """Find existing bookings that conflict with given slots."""
        conflicts = []

        for slot in slots:
            # Query for approved/in-progress bookings on the same date
            result = await self.session.execute(
                select(BookingModel)
                .options(selectinload(BookingModel.sessions))
                .where(
                    and_(
                        BookingModel.tutor_id == tutor_id,
                        BookingModel.status.in_([
                            BookingStatus.APPROVED,
                            BookingStatus.IN_PROGRESS,
                        ]),
                    )
                )
            )
            db_bookings = result.scalars().all()

            for db_booking in db_bookings:
                for db_session in db_booking.sessions:
                    if db_session.session_date.date() == slot.date.date():
                        # Check time overlap
                        session_start = datetime.strptime(db_session.session_time, "%H:%M").time()
                        # Assume 1-hour sessions for simplicity
                        from datetime import timedelta
                        session_end = (datetime.combine(datetime.today(), session_start) + timedelta(hours=1)).time()
                        existing_range = TimeRange(session_start, session_end)

                        if slot.time_range.overlaps(existing_range):
                            conflicts.append(slot)
                            break

        return conflicts

    async def create_sessions(
        self,
        booking_id: int,
        slots: List[ScheduleSlot],
    ) -> List[BookingSession]:
        """Create booking sessions from schedule slots."""
        db_sessions = []
        for slot in slots:
            db_session = BookingSessionModel(
                booking_id=booking_id,
                session_date=slot.date,
                session_time=slot.to_booking_session_time(),
                status=SessionStatus.SCHEDULED,
            )
            self.session.add(db_session)
            db_sessions.append(db_session)

        await self.session.flush()

        return [
            BookingSession(
                id=s.id,
                booking_id=s.booking_id,
                session_date=s.session_date,
                session_time=s.session_time,
                status=s.status,
            )
            for s in db_sessions
        ]

    def _to_entity(self, db_booking: BookingModel) -> Booking:
        """Convert ORM model to domain entity."""
        return Booking(
            id=db_booking.id,
            student_id=db_booking.student_id,
            tutor_id=db_booking.tutor_id,
            total_sessions=db_booking.total_sessions,
            completed_sessions=db_booking.completed_sessions,
            status=db_booking.status,
            notes=db_booking.notes,
            created_at=db_booking.created_at,
            updated_at=db_booking.updated_at,
        )
