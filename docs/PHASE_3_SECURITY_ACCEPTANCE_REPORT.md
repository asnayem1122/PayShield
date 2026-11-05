# PayShield Phase 3 Independent Security Audit & Runtime Acceptance Report

- **Date:** November 5, 2026
- **Auditor Role:** Senior Application Security Engineer, Backend Architect, PostgreSQL Security Auditor, Flutter QA Engineer
- **Repository:** `D:\Code\PayShield`
- **Branch:** `main`
- **Audit Target Commit:** `7d233e6`
- **Final Decision:** **ACCEPTED WITH LIMITATIONS** (Verified Scope Functioning; Production Boundaries Documented)

---

## 1. Repository & Git Delivery Audit

### 1.1. Working Tree & Revision History
- **Current HEAD:** Commit `7d233e6` (`docs: reconcile Phase 3 implementation report with security hardening updates`)
- **Remote Synchronization:** Up to date with `origin/main`
- **Working Tree:** Clean (zero uncommitted or untracked operational modifications)
- **Alembic Database Head:** `0004_add_session_family` applied to `payshield_dev`

### 1.2. Canonical Transaction Seed Invariants
An independent verification probe confirmed that Phase 2 canonical financial data remains 100% intact:
- **Total Canonical Transactions:** 175 records
  - **Approved:** 158 transactions | Volume = ৳ 280,200.00
  - **Review:** 14 transactions | Volume = ৳ 147,300.00
  - **Blocked:** 3 transactions | Volume = ৳ 55,000.00
- **Total Canonical Volume:** ৳ 482,500.00
- **Canonical `tx_app_1157` Remediated Amount:** ৳ 1,514.00 (exact)
- **`seed_demo_data.py --verify-only`:** `100% exact match verified across all 5 canonical entity sets. Database intact.`

---

## 2. Authentication Security Audit

### 2.1. Password Security
- **Algorithm & Work Factor:** Bcrypt (`bcrypt.hashpw` with salt rounds = 12).
- **Storage:** Only salted password hashes stored in `users.password_hash`. Plaintext passwords never stored in database or application logs.
- **Provisioning:** Passwords loaded exclusively from environment variables (`PAYSHIELD_MERCHANT_PASSWORD`, `PAYSHIELD_ANALYST_PASSWORD`, `PAYSHIELD_ADMIN_PASSWORD`). No default credentials committed to source control.
- **Fail-Closed Policy:** Missing or weak passwords (< 8 characters) cause seed and startup scripts to fail closed immediately.

### 2.2. JWT Token Lifecycle (RFC 7519)
- **Algorithm Pinning:** Pinned to `HS256`. Explicit guard disallows `alg=none` and mismatched signature algorithms.
- **Claims Verification:** Strictly verifies signature, issuer (`payshield-auth`), audience (`payshield-client`), expiration (`exp`), issued-at (`iat`), and token type (`access` vs `refresh`).
- **Access Token Expiration:** 15 minutes.
- **Database Authorization Dependency:** `get_current_user` extracts `sub` from the token and queries the active user row from PostgreSQL. Role and account status are validated against current database state on every request (client JWT claims alone are never trusted).
- **Suspended Account Defense:** Suspended users are immediately blocked with HTTP 403 Forbidden even if holding an unexpired access token.

### 2.3. Refresh Token Security & Session Family Isolation
- **Storage:** Refresh token JTIs stored in `auth_sessions`. Raw refresh token strings are never persisted.
- **Atomic Concurrency Protection:** `AuthSessionRepository.get_by_jti_for_update()` utilizes `SELECT ... FOR UPDATE` row locks to serialize concurrent refresh requests and eliminate race conditions.
- **Token Rotation:** Every refresh invalidates the presented JTI and mints a fresh token pair.
- **Replay / Reuse Detection:** Presenting an already-revoked refresh token revokes **only** the affected session family (`family_id`), isolating and terminating the compromised client device's lineage while keeping sessions on other devices (e.g., mobile vs web) active.
- **Audit Logging:** Logs `REFRESH_TOKEN_REUSE_DETECTED` with family ID, compromised JTI, and revoked session count.

### 2.4. Rate Limiting Evaluation
- **Implementation:** Thread-safe sliding-window counter in `app.core.rate_limiter.py` restricting `/api/v1/auth/login` to 10 requests per minute per IP.
- **Operational Boundary (Finding SEC-01):** The current in-memory dictionary is ideal for single-process development and academic demonstration, but resets on process restart and does not synchronize across distributed Uvicorn workers or multi-instance container clusters.

---

## 3. Role-Based Access Control (RBAC) & IDOR Audit

### 3.1. Endpoint Authorization Matrix
| Endpoint | Method | Merchant | Analyst | Admin | Observed Security Enforcement |
|---|---|:---:|:---:|:---:|---|
| `/api/v1/auth/login` | POST | Permitted | Permitted | Permitted | Unauthenticated entry point; rate-limited. |
| `/api/v1/auth/me` | GET | Own | Own | Own | Returns authenticated profile from DB. |
| `/api/v1/auth/refresh` | POST | Own | Own | Own | Rotates token within active session family. |
| `/api/v1/auth/logout` | POST | Own | Own | Own | Revokes active session family. |
| `/api/v1/dashboard/summary` | GET | Scoped | All | All | Merchant query filters by `merchant_id`. |
| `/api/v1/dashboard/risk-distribution` | GET | Scoped | All | All | Merchant query filters by `merchant_id`. |
| `/api/v1/dashboard/recent-transactions` | GET | Scoped | All | All | Merchant query filters by `merchant_id`. |
| `/api/v1/transactions` | GET | Scoped | All | All | Merchant query filters by `merchant_id`. |
| `/api/v1/transactions/{reference}` | GET | Scoped | All | All | Cross-tenant lookup returns **404 Not Found**. |
| `/api/v1/transactions` | POST | Scoped | Denied | Allowed | Forces `merchant_id = current_user.merchant_id`. |
| `/api/v1/transactions/{reference}/status` | PATCH | **403** | Allowed | Allowed | Merchant status modification denied. |
| `/api/v1/cases` | GET | **403** | Allowed | Allowed | Case review restricted to analysts/admins. |
| `/api/v1/cases/{id}` | GET | **403** | Allowed | Allowed | Detail view restricted to analysts/admins. |
| `/api/v1/cases/{id}` | PATCH | **403** | Allowed | Allowed | Resolution update restricted to analysts/admins. |
| `/api/v1/audit/logs` | GET | **403** | Allowed | Allowed | Audit log inspection restricted to analysts/admins. |

### 3.2. IDOR Prevention & Anti-Enumeration
1. **Query Parameter Tampering:** When a `MERCHANT` user queries `GET /api/v1/transactions` or `GET /api/v1/dashboard/*` with `?merchant_id=<other_merchant_id>`, the server overrides the query parameter with the authenticated `current_user.merchant_id`.
2. **Payload Tampering on Ingestion:** When a `MERCHANT` calls `POST /api/v1/transactions` with a spoofed `merchant_id` in the JSON body, the service layer strictly binds the transaction to `current_user.merchant_id`.
3. **Cross-Tenant Reference Probing:** Requesting a transaction belonging to another merchant via `GET /api/v1/transactions/{reference}` returns **HTTP 404 Not Found**, preventing enumeration of transaction references across tenants.
4. **Account Enumeration Defense:** Probing `/api/v1/auth/login` with nonexistent emails vs valid emails with wrong passwords vs suspended accounts returns identical HTTP 401 Problem Details (`"detail": "Invalid email or password"`) with constant-time dummy hashing.

---

## 4. PostgreSQL Security Audit (`payshield_app`)

Live permission probes executed against the PostgreSQL database under the runtime role `payshield_app`:

| Probe Target | Operation | Expected | Actual Result | Status |
|---|---|---|---|:---:|
| Schema / DDL | `CREATE TABLE probe_test` | Denied | Denied (`ProgrammingError: permission denied for schema public`) | **PASS** |
| Schema / DDL | `DROP TABLE transactions` | Denied | Denied (`ProgrammingError: must be owner of table transactions`) | **PASS** |
| Schema / DDL | `ALTER TABLE transactions` | Denied | Denied (`ProgrammingError: must be owner of table transactions`) | **PASS** |
| Table DML | `TRUNCATE transactions` | Denied | Denied (`ProgrammingError: permission denied for table transactions`) | **PASS** |
| Table DML | `DELETE FROM transactions` | Denied | Denied (`ProgrammingError: permission denied for table transactions`) | **PASS** |
| Table DML | `DELETE FROM audit_logs` | Denied | Denied (`ProgrammingError: permission denied for table audit_logs`) | **PASS** |
| Table DML | `DELETE FROM users` | Denied | Denied (`ProgrammingError: permission denied for table users`) | **PASS** |
| Table DML | `DELETE FROM auth_sessions` | Denied | Denied (`ProgrammingError: permission denied for table auth_sessions`) | **PASS** |
| Column Update | `UPDATE transactions.merchant_id` | Denied | Denied (`ProgrammingError: permission denied for table transactions`) | **PASS** |
| Column Update | `UPDATE transactions.amount` | Denied | Denied (`ProgrammingError: permission denied for table transactions`) | **PASS** |
| Column Update | `UPDATE users.role` | Denied | Denied (`ProgrammingError: permission denied for table users`) | **PASS** |
| Column Update | `UPDATE users.email` | Denied | Denied (`ProgrammingError: permission denied for table users`) | **PASS** |
| Column Update | `UPDATE users.merchant_id` | Denied | Denied (`ProgrammingError: permission denied for table users`) | **PASS** |
| Column Update | `UPDATE auth_sessions.family_id` | Denied | Denied (`ProgrammingError: permission denied for table auth_sessions`) | **PASS** |
| Column Update | `UPDATE auth_sessions.user_id` | Denied | Denied (`ProgrammingError: permission denied for table auth_sessions`) | **PASS** |
| Table Update | `UPDATE risk_assessments` | Denied | Denied (`ProgrammingError: permission denied for table risk_assessments`) | **PASS** |
| Table Update | `UPDATE audit_logs` | Denied | Denied (`ProgrammingError: permission denied for table audit_logs`) | **PASS** |
| Column Update | `UPDATE transactions.transaction_status` | Permitted | Permitted as expected | **PASS** |
| Column Update | `UPDATE users.password_hash` | Permitted | Permitted as expected | **PASS** |
| Column Update | `UPDATE users.failed_login_attempts` | Permitted | Permitted as expected | **PASS** |
| Column Update | `UPDATE auth_sessions.revoked_at` | Permitted | Permitted as expected | **PASS** |

**PostgreSQL Audit Verdict:** **100% OF PERMISSION PROBES PASSED**. The database least-privilege model is enforced at the database kernel level.

---

## 5. Flutter Client Security & Runtime Audit

1. **Token Storage**: Implemented via [`TokenStorage`](file:///d:/Code/PayShield/mobile/lib/features/auth/data/token_storage.dart) abstract interface. Production implementation [`SecureTokenStorage`](file:///d:/Code/PayShield/mobile/lib/features/auth/data/token_storage.dart) wraps `flutter_secure_storage` with Android Keystore (`resetOnError: true`) and iOS Keychain. Plain `SharedPreferences` is used strictly for non-sensitive theme preferences.
2. **Bearer Interceptor**: [`ApiClient`](file:///d:/Code/PayShield/mobile/lib/core/network/api_client.dart) automatically injects `Authorization: Bearer <access_token>` into authenticated requests.
3. **Single-Flight Refresh Coalescing**: `ApiClient._refreshAccessToken()` wraps refresh execution in an in-flight future (`_refreshFuture`). Parallel 401s await the identical refresh flight, eliminating token rotation concurrency races.
4. **Guaranteed Local Teardown**: `AuthController.logout()` wraps token clearance in a `try ... finally` block, ensuring local state transitions to `AuthUnauthenticated` and tokens are purged even if network or server errors occur.
5. **Static Analysis & Test Suite**:
   - `flutter analyze`: **0 issues found** (clean analysis in 117.3s).
   - `flutter test`: **47 tests passed (100% pass rate)**.

---

## 6. Live End-to-End Acceptance Verification

An independent 14-step integration test verified the complete runtime journey without modifying canonical data:

- **[Step 1] Merchant Login:** Authenticated `merchant@techpulse.bd`; returned access and refresh tokens.
- **[Step 2] Merchant Dashboard Scoping:** Summary metrics scoped strictly to merchant transactions; client query parameter spoofing overridden.
- **[Step 3] Merchant Transaction View:** Read own transaction successfully.
- **[Step 4] Merchant Case Access Denied:** Accessing `/api/v1/cases` returned **HTTP 403 Forbidden**.
- **[Step 5] Analyst Login:** Authenticated `analyst.shafiq@payshield.internal`.
- **[Step 6] Analyst Case Review:** Retrieved list of open/review cases.
- **[Step 7 & 8] Analyst Case Resolution:** Updated case resolution note and status to `IN_REVIEW`.
- **[Step 9] Audit Trail Verification:** Database verified `CASE_WORKFLOW_UPDATED` event persisted with `actor_type="ANALYST"`. Case restored to original status for clean hygiene.
- **[Step 10 & 11] Admin Verification:** Authenticated `admin.nayem@payshield.internal`; verified administrative access to cases and transactions.
- **[Step 12 & 13] Logout & Invalidation:** Logged out Device A; verified refresh token rejected with **HTTP 401**.
- **[Step 14] Multi-Device Session Isolation:** Device 1 and Device 2 logged in independently. Device 1 logged out. Device 1 refresh failed (401); Device 2 refresh succeeded (200), confirming independent device session family isolation.

---

## 7. Security Findings & Classification

### Finding SEC-01: In-Memory Sliding-Window Rate Limiter
- **Classification:** **LOW / INFORMATIONAL**
- **Affected File:** `backend/app/core/rate_limiter.py`
- **Observed Behavior:** IP rate limiting is stored in an in-memory dictionary.
- **Why It Matters:** Resets upon server restart and does not synchronize across multi-worker Uvicorn processes or horizontal container replicas.
- **Recommended Remediation:** For distributed production deployments, swap in a Redis-backed sliding-window counter and configure trusted reverse-proxy header middleware (`ProxyHeadersMiddleware`).
- **Production Blocker:** No for academic demonstration; yes for multi-instance production.

### Finding SEC-02: Permissive Development CORS Configuration
- **Classification:** **MEDIUM**
- **Affected File:** `backend/app/main.py`
- **Observed Behavior:** Configured with `allow_origins=["*"]` and `allow_credentials=True`.
- **Why It Matters:** Browsers disallow wildcard origins when credentials are included under strict CORS specifications. Works seamlessly for Flutter Mobile and Desktop, but causes browser rejections if deployed as a public web application.
- **Recommended Remediation:** Restrict `allow_origins` to explicit console origins in staging and production (e.g., `["https://console.payshield.internal"]`).
- **Production Blocker:** No for mobile/desktop demonstration; yes for public web deployment.

---

## 8. Final Acceptance Decision & Sign-off

### Overall Decision: **ACCEPTED WITH LIMITATIONS**

1. **Role Enforcement:** All three roles (`MERCHANT`, `ANALYST`, `ADMIN`) operate with strict server-side authorization.
2. **Tenant Isolation:** Merchant IDOR vulnerability is completely mitigated via query-level filtering and 404 anti-enumeration.
3. **Session Security:** Token rotation, session family isolation, and multi-device replay attack defenses operate cleanly.
4. **Database Hardening:** PostgreSQL `payshield_app` permissions enforce zero-trust immutability across non-authorized columns and tables.
5. **Academic Demonstration Readiness:** The system is **100% READY** for a controlled university demonstration.
6. **Production Readiness:** Transition to production requires replacing in-memory rate limiting with Redis and tightening CORS origins.
