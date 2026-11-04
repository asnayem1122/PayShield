"""0001_initial_schema: Initial relational schema and least-privilege permissions.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-11-04 12:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create table 'merchants'
    op.create_table(
        "merchants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="chk_merchants_nonblank_name"),
        sa.CheckConstraint("length(trim(category)) > 0", name="chk_merchants_nonblank_category"),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')", name="chk_merchants_valid_status"),
    )
    op.create_index("ix_merchants_status", "merchants", ["status"])

    # 2. Create table 'transactions'
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("merchant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("counterparty_name", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="BDT", nullable=False),
        sa.Column("transaction_status", sa.String(length=20), nullable=False),
        sa.Column("device_model", sa.String(length=100), nullable=True),
        sa.Column("location_city", sa.String(length=100), nullable=True),
        sa.Column("is_location_anomaly", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("recommended_action", sa.String(length=20), nullable=False),
        sa.Column("channel", sa.String(length=50), server_default="MOBILE_APP", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], name="fk_transactions_merchant_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("reference", name="uq_transactions_reference"),
        sa.CheckConstraint("length(trim(reference)) > 0", name="chk_transactions_nonblank_reference"),
        sa.CheckConstraint("length(trim(counterparty_name)) > 0", name="chk_transactions_nonblank_counterparty"),
        sa.CheckConstraint("amount > 0.00", name="chk_transactions_positive_amount"),
        sa.CheckConstraint("currency = 'BDT'", name="chk_transactions_bdt_currency_only"),
        sa.CheckConstraint("transaction_status IN ('APPROVED', 'REVIEW', 'BLOCKED')", name="chk_transactions_valid_status"),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="chk_transactions_valid_risk_score"),
        sa.CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_transactions_valid_risk_level"),
        sa.CheckConstraint("recommended_action IN ('APPROVE', 'REVIEW', 'BLOCK')", name="chk_transactions_valid_action"),
        sa.CheckConstraint(
            """
            (risk_score >= 0 AND risk_score <= 39 AND risk_level = 'LOW') OR
            (risk_score >= 40 AND risk_score <= 74 AND risk_level = 'MEDIUM') OR
            (risk_score >= 75 AND risk_score <= 100 AND risk_level = 'HIGH')
            """,
            name="chk_transactions_score_level",
        ),
        sa.CheckConstraint(
            """
            (risk_level = 'LOW' AND recommended_action = 'APPROVE') OR
            (risk_level = 'MEDIUM' AND recommended_action = 'REVIEW') OR
            (risk_level = 'HIGH' AND recommended_action = 'BLOCK')
            """,
            name="chk_transactions_level_action",
        ),
    )
    op.create_index("ix_transactions_merchant_id", "transactions", ["merchant_id"])
    op.create_index("ix_transactions_status", "transactions", ["transaction_status"])
    op.create_index("ix_transactions_risk_level", "transactions", ["risk_level"])
    op.create_index("ix_transactions_created_at", "transactions", [sa.text("created_at DESC")])

    # 3. Create table 'risk_assessments'
    op.create_table(
        "risk_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_score", sa.Integer(), nullable=True),
        sa.Column("raw_score", sa.Integer(), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("is_score_clamped", sa.Boolean(), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("recommended_action", sa.String(length=20), nullable=False),
        sa.Column("scoring_method", sa.String(length=50), nullable=False),
        sa.Column("policy_version", sa.String(length=20), server_default="1.0.0", nullable=False),
        sa.Column("risk_factors", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("feature_contributions", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], name="fk_risk_assessments_transaction_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("transaction_id", "scoring_method", "policy_version", name="uq_risk_assessment_tx_method_version"),
        sa.CheckConstraint("raw_score IS NULL OR (raw_score >= 0 AND raw_score <= 110)", name="chk_risk_assessments_valid_raw_score"),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="chk_risk_assessments_valid_risk_score"),
        sa.CheckConstraint("risk_level IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_risk_assessments_valid_risk_level"),
        sa.CheckConstraint("recommended_action IN ('APPROVE', 'REVIEW', 'BLOCK')", name="chk_risk_assessments_valid_action"),
        sa.CheckConstraint("scoring_method IN ('CANONICAL_SEED', 'HEURISTIC_RULES_V1')", name="chk_risk_assessments_valid_method"),
        sa.CheckConstraint(
            """
            (risk_score >= 0 AND risk_score <= 39 AND risk_level = 'LOW') OR
            (risk_score >= 40 AND risk_score <= 74 AND risk_level = 'MEDIUM') OR
            (risk_score >= 75 AND risk_score <= 100 AND risk_level = 'HIGH')
            """,
            name="chk_risk_assessments_score_level",
        ),
        sa.CheckConstraint(
            """
            (risk_level = 'LOW' AND recommended_action = 'APPROVE') OR
            (risk_level = 'MEDIUM' AND recommended_action = 'REVIEW') OR
            (risk_level = 'HIGH' AND recommended_action = 'BLOCK')
            """,
            name="chk_risk_assessments_level_action",
        ),
        sa.CheckConstraint(
            """
            (scoring_method = 'CANONICAL_SEED' AND 
             base_score IS NULL AND 
             raw_score IS NULL AND 
             is_score_clamped IS NULL)
            OR
            (scoring_method = 'HEURISTIC_RULES_V1' AND 
             base_score = 10 AND 
             raw_score >= 0 AND raw_score <= 110 AND 
             is_score_clamped IS NOT NULL AND
             ((raw_score > 100 AND risk_score = 100 AND is_score_clamped = TRUE) OR
              (raw_score <= 100 AND risk_score = raw_score AND is_score_clamped = FALSE)))
            """,
            name="chk_risk_assessments_scoring_metadata",
        ),
    )
    op.create_index("ix_risk_assessments_tx_id", "risk_assessments", ["transaction_id"])
    op.create_index("ix_risk_assessments_scoring_method", "risk_assessments", ["scoring_method"])

    # 4. Create table 'analyst_cases'
    op.create_table(
        "analyst_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_status", sa.String(length=20), server_default="OPEN", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="MEDIUM", nullable=False),
        sa.Column("trigger_reason", sa.String(length=100), nullable=False),
        sa.Column("assigned_analyst", sa.String(length=100), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], name="fk_analyst_cases_transaction_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("transaction_id", name="uq_analyst_cases_transaction_id"),
        sa.CheckConstraint("case_status IN ('OPEN', 'IN_REVIEW', 'RESOLVED')", name="chk_analyst_cases_valid_status"),
        sa.CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_analyst_cases_valid_priority"),
        sa.CheckConstraint(
            """
            trigger_reason IN (
                'UNUSUAL_HOUR', 'NEW_DEVICE', 'VELOCITY_WARN', 'HIGH_AMOUNT',
                'DISTANCE_DELTA', 'MULTIPLE_CARDS', 'DEVICE_MISMATCH', 'NEW_ACCOUNT',
                'OFF_HOURS', 'MANUAL_FLAG', 'SCORE_THRESHOLD_EXCEEDED'
            )
            """,
            name="chk_analyst_cases_valid_trigger_reason",
        ),
        sa.CheckConstraint(
            """
            (case_status = 'RESOLVED' AND resolved_at IS NOT NULL) OR
            (case_status <> 'RESOLVED' AND resolved_at IS NULL)
            """,
            name="chk_analyst_cases_resolved",
        ),
    )
    op.create_index("ix_analyst_cases_status", "analyst_cases", ["case_status"])
    op.create_index("ix_analyst_cases_created_at", "analyst_cases", [sa.text("created_at DESC")])

    # 5. Create table 'audit_logs'
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_type", sa.String(length=50), nullable=False),
        sa.Column("actor_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("idempotency_key", sa.String(length=150), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_audit_logs_idempotency_key"),
        sa.CheckConstraint("actor_type IN ('SYSTEM', 'ANALYST', 'MERCHANT', 'ADMIN')", name="chk_audit_logs_valid_actor_type"),
        sa.CheckConstraint("length(trim(action)) > 0", name="chk_audit_logs_nonblank_action"),
        sa.CheckConstraint("length(trim(entity_type)) > 0", name="chk_audit_logs_nonblank_entity_type"),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", [sa.text("created_at DESC")])

    # 6. Apply strict least-privilege permissions to payshield_app
    # Revoke broad table privileges
    op.execute("REVOKE ALL PRIVILEGES ON TABLE merchants FROM payshield_app")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE transactions FROM payshield_app")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE risk_assessments FROM payshield_app")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE analyst_cases FROM payshield_app")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE audit_logs FROM payshield_app")

    # Table SELECT grants
    op.execute("GRANT SELECT ON TABLE merchants TO payshield_app")
    op.execute("GRANT SELECT ON TABLE transactions TO payshield_app")
    op.execute("GRANT SELECT ON TABLE risk_assessments TO payshield_app")
    op.execute("GRANT SELECT ON TABLE analyst_cases TO payshield_app")
    op.execute("GRANT SELECT ON TABLE audit_logs TO payshield_app")

    # Table INSERT grants (merchants is read-only for payshield_app; no INSERT)
    op.execute("GRANT INSERT ON TABLE transactions TO payshield_app")
    op.execute("GRANT INSERT ON TABLE risk_assessments TO payshield_app")
    op.execute("GRANT INSERT ON TABLE analyst_cases TO payshield_app")
    op.execute("GRANT INSERT ON TABLE audit_logs TO payshield_app")

    # Explicitly revoke table-level UPDATE before column-level grants
    op.execute("REVOKE UPDATE ON TABLE transactions FROM payshield_app")
    op.execute("REVOKE UPDATE ON TABLE analyst_cases FROM payshield_app")

    # Grant strictly approved column-level UPDATE
    op.execute("GRANT UPDATE (transaction_status, updated_at) ON TABLE transactions TO payshield_app")
    op.execute("GRANT UPDATE (case_status, resolution_note, resolved_at, updated_at) ON TABLE analyst_cases TO payshield_app")


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table("audit_logs")
    op.drop_table("analyst_cases")
    op.drop_table("risk_assessments")
    op.drop_table("transactions")
    op.drop_table("merchants")
