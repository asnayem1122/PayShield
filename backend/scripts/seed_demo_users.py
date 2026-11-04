"""Idempotent seed script for PayShield canonical demo users.

Provisions the three required canonical accounts:
1. Merchant: merchant@techpulse.bd (linked to canonical PayShield Demo Merchant)
2. Analyst: analyst.shafiq@payshield.internal (unlinked, ANALYST role)
3. Admin: admin.nayem@payshield.internal (unlinked, ADMIN role)

Supports --verify-only flag to check integrity without modifying data.
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
from app.models.merchant import Merchant
from app.models.user import User

DEFAULT_DEMO_PASSWORD = os.getenv("PAYSHIELD_DEMO_PASSWORD", "PayShield2026!")

CANONICAL_USERS = [
    {
        "email": "merchant@techpulse.bd",
        "full_name": "TechPulse Demo Merchant",
        "role": "MERCHANT",
        "status": "ACTIVE",
        "requires_merchant": True,
        "default_password": os.getenv("PAYSHIELD_MERCHANT_PASSWORD", DEFAULT_DEMO_PASSWORD),
    },
    {
        "email": "analyst.shafiq@payshield.internal",
        "full_name": "Shafiqul Islam",
        "role": "ANALYST",
        "status": "ACTIVE",
        "requires_merchant": False,
        "default_password": os.getenv("PAYSHIELD_ANALYST_PASSWORD", DEFAULT_DEMO_PASSWORD),
    },
    {
        "email": "admin.nayem@payshield.internal",
        "full_name": "Nayem Admin",
        "role": "ADMIN",
        "status": "ACTIVE",
        "requires_merchant": False,
        "default_password": os.getenv("PAYSHIELD_ADMIN_PASSWORD", DEFAULT_DEMO_PASSWORD),
    },
]


def seed_demo_users(verify_only: bool = False, db_url=None) -> bool:
    """Provision or verify canonical demo user accounts."""
    if db_url is None:
        url = settings.get_migration_sqlalchemy_url()
    else:
        url = db_url

    engine = create_engine(url)
    with Session(engine) as session:
        # 1. Fetch canonical merchant
        merchant_stmt = select(Merchant).where(Merchant.name == "PayShield Demo Merchant")
        demo_merchant = session.execute(merchant_stmt).scalar_one_or_none()

        if not demo_merchant:
            # Fallback to any active merchant
            demo_merchant = session.execute(
                select(Merchant).where(Merchant.status == "ACTIVE").limit(1)
            ).scalar_one_or_none()

        if not demo_merchant:
            print("ERROR: No active merchant found in database to link merchant user.")
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
                pw_hash = hash_password(spec["default_password"])
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
                        print(f"OK: User '{email}' ({existing_user.role}) is valid and verified.")

        if not verify_only:
            session.commit()
            print("Canonical demo users successfully seeded and committed.")
            return True

        return all_valid


def main():
    parser = argparse.ArgumentParser(description="Seed or verify PayShield canonical demo users.")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Check canonical user existence and attributes without modifying database.",
    )
    args = parser.parse_args()

    success = seed_demo_users(verify_only=args.verify_only)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
