"""Add is_primary, timezone, and nullable phone_number to stores table

Revision ID: 002_store_primary_and_timezone
Revises: 001_initial_schema
Create Date: 2026-11-12 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002_store_primary_and_timezone"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_primary column
    op.add_column(
        "stores",
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    # 2. Add timezone column
    op.add_column(
        "stores",
        sa.Column("timezone", sa.String(50), server_default="Asia/Kolkata", nullable=False),
    )

    # 3. Make phone_number nullable
    op.alter_column(
        "stores",
        "phone_number",
        existing_type=sa.String(15),
        nullable=True,
    )

    # 4. Partial unique index to enforce exactly one primary store per business
    op.create_index(
        "uq_store_primary_per_business",
        "stores",
        ["business_id"],
        unique=True,
        postgresql_where=sa.text("is_primary = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_store_primary_per_business", table_name="stores")
    op.alter_column(
        "stores",
        "phone_number",
        existing_type=sa.String(15),
        nullable=False,
    )
    op.drop_column("stores", "timezone")
    op.drop_column("stores", "is_primary")
