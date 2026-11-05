"""0004_add_session_family: Add family_id to auth_sessions for isolated token rotation.

Revision ID: 0004_add_session_family
Revises: 0003_create_users_table
Create Date: 2026-11-05 03:05:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0004_add_session_family"
down_revision: Union[str, None] = "0003_create_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add family_id column with default gen_random_uuid()
    op.add_column(
        "auth_sessions",
        sa.Column(
            "family_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    # 2. Add index on family_id
    op.create_index(
        "ix_auth_sessions_family_id",
        "auth_sessions",
        ["family_id"],
    )
    # 3. Ensure least-privilege permissions for payshield_app remain intact
    op.execute("GRANT SELECT, INSERT ON TABLE auth_sessions TO payshield_app")
    op.execute(
        "GRANT UPDATE (last_used_at, revoked_at) ON TABLE auth_sessions TO payshield_app"
    )


def downgrade() -> None:
    op.drop_index("ix_auth_sessions_family_id", table_name="auth_sessions")
    op.drop_column("auth_sessions", "family_id")
