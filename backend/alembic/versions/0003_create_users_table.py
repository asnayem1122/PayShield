"""0003_create_users_table: Create users and auth_sessions tables with RBAC constraints.

Revision ID: 0003_create_users_table
Revises: 0002_revoke_analyst_update
Create Date: 2026-11-05 02:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0003_create_users_table"
down_revision: Union[str, None] = "0002_revoke_analyst_update"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'ACTIVE'"),
            nullable=False,
        ),
        sa.Column(
            "merchant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchants.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "role IN ('MERCHANT', 'ANALYST', 'ADMIN')",
            name="chk_users_valid_role",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED')",
            name="chk_users_valid_status",
        ),
        sa.CheckConstraint("length(trim(email)) > 0", name="chk_users_nonblank_email"),
        sa.CheckConstraint(
            "length(trim(full_name)) > 0", name="chk_users_nonblank_name"
        ),
        sa.CheckConstraint(
            "failed_login_attempts >= 0",
            name="chk_users_nonnegative_failed_attempts",
        ),
        sa.CheckConstraint(
            "(role = 'MERCHANT' AND merchant_id IS NOT NULL) OR (role IN ('ANALYST', 'ADMIN') AND merchant_id IS NULL)",
            name="chk_users_role_merchant_match",
        ),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_merchant_id", "users", ["merchant_id"])

    # 2. Create auth_sessions table
    op.create_table(
        "auth_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_jti", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "refresh_token_jti", name="uq_auth_sessions_refresh_token_jti"
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="chk_auth_sessions_expires_after_created",
        ),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index(
        "ix_auth_sessions_refresh_token_jti", "auth_sessions", ["refresh_token_jti"]
    )

    # 3. Apply least-privilege permissions to payshield_app
    op.execute("REVOKE ALL PRIVILEGES ON TABLE users FROM payshield_app")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE auth_sessions FROM payshield_app")

    op.execute("GRANT SELECT, INSERT ON TABLE users TO payshield_app")
    op.execute(
        "GRANT UPDATE (password_hash, full_name, failed_login_attempts, locked_until, last_login_at, updated_at) "
        "ON TABLE users TO payshield_app"
    )

    op.execute("GRANT SELECT, INSERT ON TABLE auth_sessions TO payshield_app")
    op.execute(
        "GRANT UPDATE (last_used_at, revoked_at) ON TABLE auth_sessions TO payshield_app"
    )


def downgrade() -> None:
    # Revoke permissions first
    op.execute("REVOKE ALL PRIVILEGES ON TABLE auth_sessions FROM payshield_app")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE users FROM payshield_app")

    # Drop tables in reverse order
    op.drop_table("auth_sessions")
    op.drop_table("users")
