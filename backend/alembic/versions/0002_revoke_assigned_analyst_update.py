"""0002_revoke_assigned_analyst_update: Revoke UPDATE on assigned_analyst from payshield_app.

Revision ID: 0002_revoke_assigned_analyst_update
Revises: 0001_initial_schema
Create Date: 2026-11-04 18:00:00.000000
"""

from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0002_revoke_analyst_update"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Revoke column-level UPDATE on assigned_analyst from payshield_app
    # to enforce assignment immutability at runtime.
    # Preserves UPDATE on (case_status, resolution_note, resolved_at, updated_at).
    op.execute("REVOKE UPDATE (assigned_analyst) ON TABLE analyst_cases FROM payshield_app")


def downgrade() -> None:
    # Re-grant column-level UPDATE on assigned_analyst to payshield_app
    # restoring the original migration 0001 permission scope.
    op.execute("GRANT UPDATE (assigned_analyst) ON TABLE analyst_cases TO payshield_app")
