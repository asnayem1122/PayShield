# PayShield Milestone 3 / Phase 3 Implementation Report
**Authentication, JWT Security & Server-Side Role-Based Access Control (RBAC)**

- **Date:** November 5, 2026
- **Repository:** `D:\Code\PayShield`
- **Branch:** `main`
- **Baseline Commit:** `80e5d5f`
- **Latest Hardened Commit:** `3f6018f`
- **Status:** **FULLY IMPLEMENTED, HARDENED & VERIFIED**

---

## 1. Executive Summary

Milestone 3 / Phase 3 delivers complete production-grade authentication, RFC 7519 JWT session security, least-privilege PostgreSQL persistence, server-side Role-Based Access Control (RBAC), and full Flutter client integration for the PayShield fraud monitoring platform.

All requirements have been met without breaking or regressing any Phase 1 or Phase 2 capabilities. The canonical 175-transaction dataset (৳ 482,500.00 volume, exact remediated ৳ 1,514.00 for `tx_app_1157`) remains 100% intact and verified.

---

## 2. Key Architecture Components

### 2.1. Relational Schema & Alembic Migrations
Two forward and reversible migrations were created and applied to the PostgreSQL database:

1. **`0003_create_users_table.py`** (down revision `0002_revoke_analyst_update`):
   - **`users` Table**:
     - `id`: UUID Primary Key (`gen_random_uuid()`).
     - `email`: VARCHAR(255) Unique, normalized lowercase.
     - `full_name`: VARCHAR(255) Not Null.
     - `password_hash`: VARCHAR(255) Not Null (Bcrypt work factor 12; never exposed in API responses).
     - `role`: VARCHAR(50) with Check Constraint `role IN ('MERCHANT', 'ANALYST', 'ADMIN')`.
     - `status`: VARCHAR(50) with Check Constraint `status IN ('ACTIVE', 'SUSPENDED')`.
     - `merchant_id`: UUID Foreign Key to `merchants.id` (`ON DELETE RESTRICT`).
     - **Role/Merchant Linkage Constraint**:
       `CHECK ((role = 'MERCHANT' AND merchant_id IS NOT NULL) OR (role IN ('ANALYST', 'ADMIN') AND merchant_id IS NULL))`.
     - `failed_login_attempts`: Integer with Check Constraint `>= 0`.
     - `locked_until`: TIMESTAMPTZ for temporal account lockout.
     - `last_login_at`, `created_at`, `updated_at`: UTC timestamps.
   - **`auth_sessions` Table**:
     - `id`: UUID Primary Key (`gen_random_uuid()`).
     - `user_id`: UUID Foreign Key to `users.id` (`ON DELETE CASCADE`).
     - `refresh_token_jti`: VARCHAR(64) Unique (indexed).
     - `expires_at`, `last_used_at`, `revoked_at`: Session tracking timestamps.
     - Check Constraint: `expires_at > created_at`.

2. **`0004_add_session_family.py`** (down revision `0003_create_users_table`):
   - Added `family_id: UUID` (NOT NULL, default `gen_random_uuid()`, indexed via `ix_auth_sessions_family_id`) to `auth_sessions`.
   - Enables device session family isolation for token rotation and selective replay termination.

### 2.2. PostgreSQL Least-Privilege Grants
Following the project's zero-trust database permission model:
- `payshield_app` is granted `SELECT, INSERT` on `users` and `auth_sessions`.
- `payshield_app` is granted column-level `UPDATE` strictly on mutable security/profile columns:
  - `users(password_hash, full_name, failed_login_attempts, locked_until, last_login_at, updated_at)`.
  - `auth_sessions(last_used_at, revoked_at)`.
- `payshield_app` is strictly **DENIED** `UPDATE` on identity/role columns (`id`, `email`, `role`, `merchant_id`, `created_at`), preventing privilege escalation via application SQL injection.
- `payshield_app` is strictly **DENIED** `DELETE` and `TRUNCATE` on both tables.

### 2.3. Cryptographic & JWT Security Standard (RFC 7519)
- **Password Hashing**: Bcrypt with salt rounds = 12 via `app.core.security`.
- **Dynamic Configuration**: `JWT_SECRET_KEY` uses dynamic ephemeral keys in development, and enforces minimum 32 characters and rejection of weak placeholders in staging/production.
- **Access Tokens**: Short-lived (15 minutes default), signed with HMAC SHA256. Claims include `sub` (user UUID), `role`, `email`, `merchant_id`, `iss` (`payshield-auth`), `aud` (`payshield-client`), `iat`, `exp`, `jti`, and `type="access"`.
- **Refresh Tokens**: Long-lived (7 days default), signed with unique `jti`. Stored in `auth_sessions`.
- **Refresh Token Rotation with Atomic Row Lock**: Upon refresh, `SELECT ... FOR UPDATE` row locking prevents concurrency races. The presented token is revoked, and a new token pair maintaining the same `family_id` is issued.
- **Session Family Isolation**: Replay of a revoked token terminates only the affected device's session lineage (`family_id`), leaving sessions on other user devices active.
- **Strict Decoding**: Enforces algorithm (`HS256`), rejects `alg=none`, validates issuer, audience, type, and expiration timestamps.

### 2.4. Anti-Enumeration, IP Rate Limiting & RFC 9457 Problem Details
- Constant-time dummy password hashing on nonexistent usernames to prevent timing-based user enumeration.
- Identical generic error message (`"Invalid email or password"`) for non-existent users and suspended accounts.
- Thread-safe sliding-window rate limiter in `app.core.rate_limiter` restricting `/api/v1/auth/login` to 10 attempts per minute per IP address.
- Temporal account lockout (HTTP 423 Locked) engaging after 5 consecutive failed login attempts.
- All errors formatted according to RFC 9457 `application/problem+json`:
  ```json
  {
    "type": "https://payshield.internal/errors/invalid-credentials",
    "title": "Unauthorized",
    "status": 401,
    "detail": "Invalid email or password",
    "instance": "/api/v1/auth/login"
  }
  ```

### 2.5. Server-Side Role-Based Access Control (RBAC)
Enforced at the FastAPI dependency layer (`get_current_user`, `require_role`, `require_merchant_ownership`):
1. **MERCHANT**:
   - Ingests transactions strictly bound to their own `merchant_id` (client-provided spoofed `merchant_id` is automatically overridden).
   - Queries to `GET /transactions` and `GET /dashboard/*` are automatically filtered to the user's `merchant_id`.
   - Accessing a transaction belonging to another merchant returns **HTTP 404 Not Found** (anti-enumeration preventing IDOR discovery).
   - Denied access (HTTP 403 Forbidden) to `/cases/*`, `/audit/*`, and `PATCH /transactions/*/status`.
2. **ANALYST**:
   - Full read/write access to investigation cases (`/cases/*`), transaction status overrides (`PATCH /transactions/{ref}/status`), system-wide dashboard metrics, and audit logs.
   - Denied user management modifications.
3. **ADMIN**:
   - Unrestricted read/write access across all system entities, users, audit logs, and configurations.

### 2.6. Canonical Demo User Seeding (`seed_demo_users.py`)
An idempotent, verifiable seeding script was implemented using `payshield_migrator`:
- **Merchant**: `merchant@techpulse.bd` linked to `PayShield Demo Merchant` (strictly verified without arbitrary fallback).
- **Analyst**: `analyst.shafiq@payshield.internal` (unlinked).
- **Admin**: `admin.nayem@payshield.internal` (unlinked).
- Passwords supplied strictly via environment variables (`PAYSHIELD_MERCHANT_PASSWORD`, `PAYSHIELD_ANALYST_PASSWORD`, `PAYSHIELD_ADMIN_PASSWORD`).
- Supports `--verify-only`, `--verify-passwords`, and `--rotate-passwords` for non-destructive CI/CD audits and atomic credential rotation.

### 2.7. Flutter Authentication & Secure Storage Integration
1. **Token Persistence**:
   - `TokenStorage` abstract interface with `SecureTokenStorage` backed by `flutter_secure_storage` (using `AndroidOptions(resetOnError: true)` and iOS Keychain accessibility).
   - `InMemoryTokenStorage` for fast, hermetic widget and unit testing.
2. **Networking Interceptor (`ApiClient`)**:
   - Automatically injects `Authorization: Bearer <access_token>` into outgoing requests.
   - Single-flight refresh lock: concurrent 401 responses coalesce onto a single shared `Future<bool>` refresh flight, preventing refresh races.
   - Parses RFC 9457 Problem Details into user-friendly `HttpException` messages.
3. **Riverpod State Management (`AuthController`)**:
   - States: `AuthInitial`, `AuthAuthenticating`, `AuthAuthenticated`, `AuthUnauthenticated`, `AuthError`.
   - Synchronizes UI context with server-assigned roles via `demoRoleProvider`.
   - Logout wrapped in `try ... finally` block, ensuring local credential teardown even on server failure.
4. **Login Screen & Profile Screen**:
   - `LoginScreen` wires inputs to `authController.login(email, password)` with loading states and error banner rendering.
   - Password field is empty by default; helper text with static credentials has been removed.
   - "Quick Demo Role" selector prefills identity email only.
   - `ProfileScreen` displays real authenticated user identity and provides functional sign out.

---

## 3. Verification & Evidence

### 3.1. Backend Automated Test Suite
All **126 pytest tests** passed with 0 failures:
- `backend/tests/test_security_hardening.py` (8 tests): JWT secret validation, fail-closed seed env vars, password rotation workflow, session family isolation, anti-enumeration, IP rate limiting.
- `backend/tests/test_api_auth.py` (8 tests): login, lockout, token rotation, reuse revocation, logout, profile.
- `backend/tests/test_rbac_authorization.py` (7 tests): 401 unauthenticated rejection, 403 merchant role prohibitions, analyst access, admin access, scoped dashboard.
- `backend/tests/test_merchant_isolation.py` (3 tests): query scoping, 404 anti-enumeration IDOR prevention, merchant_id tamper override.
- `backend/tests/test_permissions_phase3.py` (4 tests): column-level UPDATE and table-level UPDATE/DELETE/TRUNCATE denials for `users` and `auth_sessions`.
- All 96 existing Phase 2 tests (transactions, dashboard, cases, heuristic risk scoring, seed recovery, seed verification, database lifecycle, permissions) remain 100% green.

### 3.2. Flutter Automated Test Suite
All **47 flutter_test tests** passed with 0 failures:
- `mobile/test/unit/auth_test.dart` (8 tests): `InMemoryTokenStorage`, `UserSession` JSON parsing, `AuthController` login/logout/refresh lifecycle, logout failure resilience.
- `mobile/test/unit/api_client_and_integration_test.dart` (12 tests): Money parsing, Decimal serialization, ApiClient base URLs.
- `mobile/test/unit/risk_constants_and_data_test.dart` (8 tests): Risk score bounds, canonical mock totals.
- `mobile/test/unit/theme_test.dart` (7 tests): WCAG AAA/AA contrast verification.
- `mobile/test/widgets/screen_layout_test.dart` (3 tests): 320x568 compact layout, text scaler 1.5x.
- `mobile/test/widget_test.dart` (1 test): Application smoke test.
- `flutter analyze` passed with **0 issues found**.

### 3.3. Canonical Seed Integrity Check
- `python backend/scripts/seed_demo_data.py --verify-only`:
  `100% exact match verified across all 5 canonical entity sets. Database intact.`
- `python backend/scripts/seed_demo_users.py --verify-only`:
  `OK: User 'merchant@techpulse.bd' (MERCHANT) is valid and verified.`
  `OK: User 'analyst.shafiq@payshield.internal' (ANALYST) is valid and verified.`
  `OK: User 'admin.nayem@payshield.internal' (ADMIN) is valid and verified.`

---

## 4. Documentation Reconciliation

In `docs/PAYSHIELD_MASTER_DOCUMENTATION.md`:
- Reconciled Section 20.1 roadmap table to properly designate **Milestone 3** as "Authentication, JWT Security & Server-Side RBAC" (**COMPLETED**).
- Aligned ML Model Training & Inference under Milestones 5 and 6 as originally planned in Section 15.
- Checked off Milestone 3 items in Section 21 ("Final definition of done").
- Updated `docs/API_DOCUMENTATION.md`, `docs/DATABASE_SCHEMA.md`, and `docs/DATABASE_PERMISSIONS.md`.
