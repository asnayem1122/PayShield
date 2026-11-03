# PayShield — Transaction Fraud Risk Monitoring System

> **Project Type:** Educational Android-First FinTech / Cybersecurity Prototype  
> **Documentation:** Single Source of Truth located in [`docs/PAYSHIELD_MASTER_DOCUMENTATION.md`](docs/PAYSHIELD_MASTER_DOCUMENTATION.md)  
> **Build Governance:** [`docs/ANTIGRAVITY_BUILD_RULES.md`](docs/ANTIGRAVITY_BUILD_RULES.md)

---

## 1. What is PayShield?

PayShield is a mobile-based payment fraud-risk monitoring system developed for educational and academic demonstration. The system simulates payment transactions, evaluates risk signals (e.g., velocity, unusual location, device changes), calculates fraud probability via a machine learning model, and provides categorized recommendations (`APPROVE`, `REVIEW`, `BLOCK`) with explainable risk factors.

### Educational Disclaimer
PayShield is strictly an **educational prototype**. It uses simulated synthetic data and does **not**:
- Process real monetary transactions or integrate with real card networks / payment gateways.
- Collect, transmit, or store real credit card numbers (PAN), CVVs, PINs, or banking credentials.
- Claim PCI DSS certification or production-level banking compliance.

---

## 2. Current Architecture (Milestone 0)

Milestone 0 establishes the initial repository layout and environment verification:

```text
PayShield/
├── docs/                                # Canonical documentation
│   ├── PAYSHIELD_MASTER_DOCUMENTATION.md
│   └── ANTIGRAVITY_BUILD_RULES.md
├── backend/                             # FastAPI Python service
│   ├── .venv/                           # Dedicated virtual environment (Python 3.14.8)
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py                      # Health check endpoints (/health, /api/v1/health)
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py               # Synchronous test suite via FastAPI TestClient
│   ├── .env.example                     # Environment template (secrets excluded)
│   ├── pyproject.toml                   # Project metadata and bounded constraints
│   └── requirements.lock                # Pinned dependency freeze
├── mobile/                              # Android-first Flutter application
│   ├── android/                         # Application ID: com.payshield.mobile
│   ├── lib/
│   │   └── main.dart                    # Intact starter application
│   ├── test/
│   │   └── widget_test.dart             # Starter widget test suite
│   ├── pubspec.yaml                     # Flutter package manifest
│   └── pubspec.lock                     # Committed dependency lockfile
├── .gitignore                           # Git exclusion rules
└── README.md                            # Project guide
```

---

## 3. Required Development Tools

- **Git:** 2.50+
- **Python:** 3.14.8 (or 3.12–3.14)
- **Flutter SDK:** 3.47+ (Dart 3.13+)
- **Android SDK:** Android API Level 34+ / Command-line tools
- **PostgreSQL:** 16+ (PostgreSQL 18.6 installed; database integration scheduled for Milestone 2)

---

## 4. Setup and Execution

### 4.1 Backend Setup (Python)

1. Create and activate the virtual environment (if not already created):
   ```powershell
   # From the repository root (D:\Code\PayShield)
   py -3.14 -m venv backend\.venv
   ```

2. Install dependencies:
   ```powershell
   backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock
   ```

3. Configure environment settings:
   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

4. Run the FastAPI development server:
   ```powershell
   backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *Health endpoints can be verified at:*
   - `http://127.0.0.1:8000/health`
   - `http://127.0.0.1:8000/api/v1/health`

### 4.2 Flutter Setup (Mobile)

1. Resolve Flutter packages:
   ```powershell
   cd mobile
   flutter pub get
   ```

2. Run the mobile starter app:
   ```powershell
   flutter run
   ```

---

## 5. Running Automated Tests

### 5.1 Backend Tests
Run the synchronous pytest test suite from the repository root:
```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests -v
```

### 5.2 Flutter Tests
Run static analysis and unit tests:
```powershell
cd mobile
flutter analyze
flutter test
```

---

## 6. Current Implementation Limitations & Boundaries

Milestone 0 is strictly limited to repository skeleton, environment validation, and process health checks:
- **No Database Integration:** PostgreSQL is running locally, but database tables, migrations, and connections are not yet active (scheduled for Milestone 2).
- **No Authentication:** User login, registration, roles (Merchant, Analyst, Admin), and JWT tokens are not implemented (scheduled for Milestone 3).
- **No Transaction Management or ML:** Risk scoring, scikit-learn models, and review queues are not active (scheduled for Milestones 4–6).
- **Starter Flutter UI:** The Flutter frontend is currently the untouched starter counter template; custom PayShield design tokens, themes, and screens will be built in Milestone 1.
