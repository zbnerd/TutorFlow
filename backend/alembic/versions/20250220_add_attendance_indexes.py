"""Add attendance indexes

Revision ID: 002
Revises: 001
Create Date: 2025-02-20 17:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite index on booking_sessions for attendance queries
    # This optimizes queries filtering by session_date and status (e.g., finding today's scheduled sessions)
    op.create_index(
        "ix_booking_sessions_session_date_status",
        "booking_sessions",
        ["session_date", "status"],
    )

    # Add index on attendance_checked_by for audit queries
    # This optimizes queries for tracking who checked attendance
    op.create_index(
        "ix_booking_sessions_attendance_checked_by",
        "booking_sessions",
        ["attendance_checked_by"],
    )


def downgrade() -> None:
    op.drop_index("ix_booking_sessions_attendance_checked_by", table_name="booking_sessions")
    op.drop_index("ix_booking_sessions_session_date_status", table_name="booking_sessions")
