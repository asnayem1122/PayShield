"""Idempotent seed script for PayShield canonical demo users.

Provisions the three required canonical accounts:
1. Merchant: merchant@techpulse.bd (linked to canonical PayShield Demo Merchant)
2. Analyst: analyst.shafiq@payshield.internal (unlinked, ANALYST role)
3. Admin: admin.nayem@payshield.internal (unlinked, ADMIN role)

Supports:
- --verify-only: Check user existence and attributes without modifying database.
- --verify-passwords: In verify-only mode, verify environment passwords against stored hashes.
- --rotate-passwords: Atomically update password hashes from environment, invalidate all active sessions, and record audit events.
"""

import argparse
import os
from pathlib import Path
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.audit_log import AuditLog
from app.models.merchant import Merchant
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.auth_session_repository import AuthSessionRepository

CANONICAL_USERS = [
    {
        "email": "merchant@techpulse.bd",
        "full_name": "TechPulse Demo Merchant",
        "role": "MERCHANT",
        "status": "ACTIVE",
        "requires_merchant": True,
        "env_var": "PAYSHIELD_MERCHANT_PASSWORD",
    },
    {
        "email": "analyst.shafiq@payshield.internal",
        "full_name": "Shafiqul Islam",
        "role": "ANALYST",
        "status": "ACTIVE",
        "requires_merchant": False,
        "env_var": "PAYSHIELD_ANALYST_PASSWORD",
    },
    {
        "email": "admin.nayem@payshield.internal",
        "full_name": "Nayem Admin",
        "role": "ADMIN",
        "status": "ACTIVE",
        "requires_merchant": False,
        "env_var": "PAYSHIELD_ADMIN_PASSWORD",
    },
]


def get_validated_passwords() -> dict[str, str] | None:
    """Read and validate password environment variables for canonical demo users."""
    passwords = {}
    errors = []
    for spec in CANONICAL_USERS:
        env_name = spec["env_var"]
        val = os.getenv(env_name)
        if not val or len(val.strip()) < 8:
            errors.append(
                f"Required environment variable '{env_name}' is missing or shorter than 8 characters."
            )
        else:
            passwords[spec["email"]] = val.strip()

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return None
    return passwords


def seed_demo_users(
    verify_only: bool = False,
    verify_passwords: bool = False,
    db_url=None,
) -> bool:
    """Provision or verify canonical demo user accounts."""
    if not verify_only:
        passwords = get_validated_passwords()
        if passwords is None:
            return False
    elif verify_passwords:
        passwords = get_validated_passwords()
        if passwords is None:
            return False
    else:
        passwords = None

    if db_url is None:
        url = settings.get_migration_sqlalchemy_url()
    else:
        url = db_url

    engine = create_engine(url)
    with Session(engine) as session:
        # 1. Fetch canonical merchant (Strict: no arbitrary fallback)
        merchant_stmt = select(Merchant).where(Merchant.name == "PayShield Demo Merchant")
        demo_merchant = session.execute(merchant_stmt).scalar_one_or_none()

        if not demo_merchant:
            print("ERROR: Canonical merchant 'PayShield Demo Merchant' not found in database. Run seed_demo_data.py first.")
            return False

        all_valid = True
        for spec in CANONICAL_USERS:
            email = spec["email"]
            user_stmt = select(User).where(User.email == email)
            existing_user = session.execute(user_stmt).scalar_one_or_none()

            expected_merchant_id = demo_merchant.id if spec["requires_merchant"] else None

            if existing_user is None:
                if verify_only:
                    print(f"FAILED: User '{email}' does not exist.")
                    all_valid = False
                    continue

                print(f"Creating user '{email}' ({spec['role']})...")
                pw_hash = hash_password(passwords[email])
                new_user = User(
                    email=email,
                    full_name=spec["full_name"],
                    password_hash=pw_hash,
                    role=spec["role"],
                    status=spec["status"],
                    merchant_id=expected_merchant_id,
                )
                session.add(new_user)
                session.flush()
                print(f"Created user '{email}' successfully.")
            else:
                # Validate attributes
                is_correct = (
                    existing_user.role == spec["role"]
                    and existing_user.status == spec["status"]
                    and existing_user.merchant_id == expected_merchant_id
                )
                if not is_correct:
                    if verify_only:
                        print(f"FAILED: User '{email}' has drift in role, status, or merchant_id.")
                        all_valid = False
                    else:
                        print(f"Correcting drift for user '{email}'...")
                        existing_user.role = spec["role"]
                        existing_user.status = spec["status"]
                        existing_user.merchant_id = expected_merchant_id
                        session.flush()
                else:
                    if verify_only:
                        if verify_passwords:
                            if not verify_password(passwords[email], existing_user.password_hash):
                                print(f"FAILED: User '{email}' stored password hash does not match current environment secret.")
                                all_valid = False
                            else:
                                print(f"OK: User '{email}' ({existing_user.role}) is valid, verified, and password matches.")
                        else:
                            print(f"OK: User '{email}' ({existing_user.role}) is valid and verified.")

        if not verify_only:
            session.commit()
            print("Canonical demo users successfully seeded and committed.")
            return True

        return all_valid


def rotate_demo_passwords(db_url=None) -> bool:
    """Atomically rotate demo user passwords from environment and invalidate active sessions."""
    passwords = get_validated_passwords()
    if passwords is None:
        return False

    if db_url is None:
        url = settings.get_migration_sqlalchemy_url()
    else:
        url = db_url

    engine = create_engine(url)
    with Session(engine) as session:
        for spec in CANONICAL_USERS:
            email = spec["email"]
            user_stmt = select(User).where(User.email == email)
            user = session.execute(user_stmt).scalar_one_or_none()
            if not user:
                print(f"ERROR: Cannot rotate password. User '{email}' not found in database.")
                return False

            new_pw = passwords[email]
            user.password_hash = hash_password(new_pw)
            user.failed_login_attempts = 0
            user.locked_until = None

            # Invalidate all active sessions for this user
            revoked_count = AuthSessionRepository.revoke_all_for_user(session, user.id)

            # Record audit event
            audit = AuditLog(
                actor_type=user.role,
                actor_id=str(user.id),
                action="USER_PASSWORD_ROTATED",
                entity_type="USER",
                entity_id=str(user.id),
                details={
                    "email": email,
                    "reason": "CLI_CREDENTIAL_ROTATION",
                    "revoked_sessions_count": revoked_count,
                },
            )
            AuditLogRepository.create(session, audit)
            print(f"Rotated password and revoked {revoked_count} active session(s) for '{email}'.")

        session.commit()
        print("Successfully rotated passwords and invalidated all active sessions for canonical demo users.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Seed, verify, or rotate PayShield canonical demo users.")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Check canonical user existence and attributes without modifying database.",
    )
    parser.add_argument(
        "--verify-passwords",
        action="store_true",
        help="In verify-only mode, also verify environment passwords against stored hashes.",
    )
    parser.add_argument(
        "--rotate-passwords",
        action="store_true",
        help="Rotate demo passwords using environment variables, invalidate sessions, and record audit logs.",
    )
    args = parser.parse_args()

    if args.rotate_passwords:
        success = rotate_demo_passwords()
    else:
        success = seed_demo_users(
            verify_only=args.verify_only,
            verify_passwords=args.verify_passwords,
        )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
