# PayShield Phase 3 Security Hardening & Credential Remediation Report

**Date:** November 5, 2026  
**Repository:** `D:\Code\PayShield`  
**Target Milestone:** Milestone 3 (Authentication, RBAC & Security Hardening)  
**Status:** **COMPLETED & VERIFIED**

---

## 1. Executive Summary

This report documents the corrective audit and implementation of security hardening across the PayShield authentication subsystem. All identified vulnerabilities and security defects—including hardcoded credentials in source files, weak default secrets, session family race conditions, unhandled logout errors, account enumeration vectors, and lack of login rate limiting—have been completely resolved without disturbing existing Milestone 1 and Milestone 2 functionality or canonical demo data.

---

## 2. Remediated Vulnerabilities & Technical Fixes

### 2.1. P1 — Removal of Exposed Demo Passwords
- **Vulnerability**: `DEFAULT_DEMO_PASSWORD = "PayShield2026!"` was hardcoded in `backend/scripts/seed_demo_users.py`, prefilled in Flutter's `LoginScreen`, displayed in helper text, and hardcoded throughout tests.
- **Remediation**:
  1. Removed `DEFAULT_DEMO_PASSWORD` from `backend/scripts/seed_demo_users.py`.
  2. Required explicit environment variables for each account:
     - `PAYSHIELD_MERCHANT_PASSWORD`
     - `PAYSHIELD_ANALYST_PASSWORD`
     - `PAYSHIELD_ADMIN_PASSWORD`
  3. Added policy checks enforcing minimum 8 characters per password. Missing or weak variables fail closed immediately.
  4. Added `--rotate-passwords` CLI command to atomically rehash passwords with Bcrypt (12 rounds), invalidate all active user sessions (`AuthSessionRepository.revoke_all_for_user`), and log `USER_PASSWORD_ROTATED` audit events.
  5. Updated Flutter `LoginScreen` (`mobile/lib/features/auth/presentation/login_screen.dart`):
     - `_passwordController` initializes empty.
     - Role quick-switcher only sets `_emailController.text` and clears password.
     - Removed credential helper text completely.
  6. Replaced hardcoded test passwords in `backend/tests/test_api_auth.py` and `conftest.py` with dynamic test environment fixtures.

### 2.2. P1 — Hardening JWT & Database Secret Configuration
- **Vulnerability**: Static default JWT secret string was committed in `backend/app/core/config.py`, and default dev passwords could be deployed accidentally to production.
- **Remediation**:
  1. Updated `backend/app/core/config.py`:
     - Replaced committed default secret keys with `secrets.token_urlsafe(32)` dynamic generation for development.
     - Implemented Pydantic `@model_validator(mode="after")` enforcing:
       - Secret key length $\ge 32$ characters (256-bit entropy).
       - In `staging` and `production`, fails closed if `JWT_SECRET_KEY` is missing or matches known insecure placeholder words (`"insecure"`, `"change_this"`, `"default"`, `"secret"`, `"placeholder"`, etc.).
       - In `staging` and `production`, fails closed if default development database passwords are detected.
  2. Sanitized `backend/.env.example` with clear non-functional placeholder values.

### 2.3. P1 — Refresh Token Rotation Concurrency & Session Family Isolation
- **Vulnerability**: Concurrent 401s in Flutter triggered simultaneous refresh calls leading to false reuse detection. Replay attack revocation terminated all sessions across all devices for the user rather than isolating the compromised device lineage.
- **Remediation**:
  1. **Alembic Migration `0004_add_session_family.py`**:
     - Added `family_id: UUID` (NOT NULL, default `gen_random_uuid()`) with index `ix_auth_sessions_family_id` to `auth_sessions`.
     - Reversible downgrade support and preserved least-privilege permissions for `payshield_app`.
  2. **Atomic Token Row Lock**:
     - `AuthSessionRepository.get_by_jti_for_update()` executes `SELECT ... FOR UPDATE` to serialize concurrent rotation attempts.
  3. **Session Family Isolation**:
     - Initial `/auth/login` creates a new `family_id`.
     - Token rotation preserves the existing `family_id`.
     - Token reuse detection revokes **only** the affected session family (`revoke_family`), ensuring valid sessions on other devices (e.g. Web vs Mobile) remain active.
     - Logs `REFRESH_TOKEN_REUSE_DETECTED` security audit events.
  4. **Flutter Single-Flight Refresh Coalescing**:
     - In `mobile/lib/core/network/api_client.dart`, added `_refreshFuture` mutex. Concurrent 401 responses coalesce and await the single in-flight refresh `Future<bool>`.
     - Request retries use the newly issued access token.
     - Avoided refreshing on `/auth` routes to prevent loops.

### 2.4. P1 — Logout Failure Resilience
- **Vulnerability**: If `/auth/logout` failed due to network errors or 401, client tokens were not evicted and user was stuck authenticated.
- **Remediation**:
  1. In `mobile/lib/features/auth/presentation/auth_controller.dart`, wrapped logout teardown in a `try ... finally` block:
     ```dart
     try {
       final refreshToken = await tokenStorage.getRefreshToken();
       if (refreshToken != null && refreshToken.isNotEmpty) {
         await repository.logout(refreshToken);
       }
     } catch (_) {
       // Ignore network/server errors during logout
     } finally {
       await tokenStorage.clearTokens();
       state = const AuthUnauthenticated();
     }
     ```
  2. In `backend/app/services/auth_service.py`, logout revokes only the caller's specific session family when a refresh token is supplied.

### 2.5. P2 — Anti-Account Enumeration & Rate Limiting
- **Vulnerability**: Suspended accounts returned 403 `Account Suspended`, disclosing valid user existence to unauthenticated callers. No rate limiting existed on `/auth/login`.
- **Remediation**:
  1. Constant-time dummy verification executed for nonexistent users.
  2. Suspended accounts execute password verification and return generic 401 `"Invalid email or password"` identical to nonexistent accounts. Exact failure reason (`ACCOUNT_SUSPENDED`) is logged internally in `audit_logs` with actor `SYSTEM`.
  3. Implemented thread-safe sliding-window rate limiter in `backend/app/core/rate_limiter.py` limiting `/auth/login` to 10 requests per minute per IP. Excess attempts return HTTP 429 with RFC 9457 Problem Detail.

### 2.6. P2 — Removal of Merchant Seed Fallback
- **Vulnerability**: `seed_demo_users.py` fell back to `SELECT * FROM merchants LIMIT 1` if canonical merchant was missing.
- **Remediation**:
  - Replaced fallback with strict lookup for `PayShield Demo Merchant`. If missing, the script aborts atomically with an error.

---

## 3. Verification & Acceptance Evidence

### 3.1. Backend Automated Test Suite
- Total tests: **126 passed** (0 failures, 1 deprecation warning from testclient):
  - `test_security_hardening.py`: 8 tests (JWT validation, password rotation, session family isolation, anti-enumeration, IP rate limiting)
  - `test_api_auth.py`: 8 tests (login, me, refresh, logout, RFC 9457 problem details)
  - `test_permissions.py`, `test_permissions_phase2.py`, `test_permissions_phase3.py`: 31 tests (PostgreSQL least-privilege security)
  - `test_merchant_isolation.py`, `test_rbac_authorization.py`: 10 tests (tenant scoping & role enforcement)
  - `test_seed_recovery.py`, `test_seed_verification.py`: 34 tests (canonical data integrity)

### 3.2. Database & Canonical Data Integrity
- Executed `python backend/scripts/seed_demo_data.py --verify-only`:
  - **100% exact match verified across all 5 canonical entity sets.**
  - Canonical 175 transactions, total volume ৳ 482,500.00 intact.
- Executed `python backend/scripts/seed_demo_users.py --verify-only`:
  - **All 3 canonical users verified.**
- Executed `python backend/scripts/seed_demo_users.py --verify-only --verify-passwords`:
  - **All 3 password hashes verified.**

### 3.3. Flutter Client Verification
- Executed `flutter analyze`: **No issues found! (0 warnings, 0 errors)**
- Executed `flutter test`: **47 tests passed (100% pass rate)** including:
  - Single-flight refresh coalescing and error handling
  - Logout resilience under backend 500 error
  - WCAG contrast ratios and layout tests
  - Decimal-safe money parser & 175-transaction offline mock

---

## 4. Summary of Files Changed

| File | Status | Description |
|---|---|---|
| `backend/alembic/versions/0004_add_session_family.py` | Created | Forward migration adding `family_id` to `auth_sessions` |
| `backend/app/core/rate_limiter.py` | Created | Sliding-window in-memory IP rate limiter |
| `backend/tests/test_security_hardening.py` | Created | Comprehensive security hardening test suite |
| `backend/app/models/auth_session.py` | Modified | Added `family_id` column and index |
| `backend/app/repositories/auth_session_repository.py` | Modified | Added row locking `get_by_jti_for_update` and `revoke_family` |
| `backend/app/services/auth_service.py` | Modified | Implemented session family rotation, anti-enumeration, and reuse isolation |
| `backend/app/api/v1/auth.py` | Modified | Added rate limiting and anti-enumeration error masking |
| `backend/app/core/config.py` | Modified | Dynamic ephemeral keys, length and placeholder validation |
| `backend/scripts/seed_demo_users.py` | Modified | Removed static passwords, added env validation, strict merchant check, `--rotate-passwords` |
| `backend/.env.example` | Modified | Sanitized example configuration |
| `backend/tests/conftest.py` | Modified | Added dynamic test secrets and rate limiter fixtures |
| `backend/tests/test_api_auth.py` | Modified | Cleaned hardcoded password strings |
| `mobile/lib/core/network/api_client.dart` | Modified | Implemented single-flight refresh coalescing |
| `mobile/lib/features/auth/presentation/login_screen.dart` | Modified | Removed password prefill and helper text |
| `mobile/lib/features/auth/presentation/auth_controller.dart` | Modified | Implemented guaranteed local logout teardown |
| `mobile/test/unit/auth_test.dart` | Modified | Added logout resilience test and cleaned credentials |
| `docs/DATABASE_SCHEMA.md` | Modified | Documented `auth_sessions.family_id` and migration 0004 |
| `docs/API_DOCUMENTATION.md` | Modified | Documented rate limiting, anti-enumeration, and family rotation |
| `docs/PAYSHIELD_MASTER_DOCUMENTATION.md` | Modified | Updated Milestone 3 status to completed with 126 backend tests |
