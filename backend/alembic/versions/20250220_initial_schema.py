"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-02-20 17:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("kakao_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("email", sa.String(255)),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("profile_url", sa.String(500)),
        sa.Column("phone", sa.String(20)),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_kakao_id", "users", ["kakao_id"])

    # Create tutors table
    op.create_table(
        "tutors",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("bio", sa.Text()),
        sa.Column("subjects", postgresql.ARRAY(sa.String()), default=[]),
        sa.Column("region", sa.String(100)),
        sa.Column("hourly_rate", sa.Integer(), nullable=False),
        sa.Column("no_show_policy", sa.String(20), nullable=False, server_default="FULL_DEDUCTION"),
        sa.Column("cancellation_hours", sa.Integer(), nullable=False, server_default=24),
        sa.Column("bank_name", sa.String(50)),
        sa.Column("bank_account", sa.String(50)),
        sa.Column("bank_holder", sa.String(50)),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # Create students table
    op.create_table(
        "students",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("grade", sa.Integer()),
        sa.Column("parent_name", sa.String(50)),
        sa.Column("parent_phone", sa.String(20)),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # Create available_slots table
    op.create_table(
        "available_slots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tutor_id",
            postgresql.UUID(as_uuid=True),
            ForeignKey("tutors.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.String(5), nullable=False),
        sa.Column("end_time", sa.String(5), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("tutor_id", "day_of_week", "start_time", "end_time"),
    )
    op.create_index("ix_available_slots_tutor_id", "available_slots", ["tutor_id"])


def downgrade() -> None:
    op.drop_index("ix_available_slots_tutor_id", table_name="available_slots")
    op.drop_table("available_slots")
    op.drop_table("students")
    op.drop_table("tutors")
    op.drop_index("ix_users_kakao_id", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
