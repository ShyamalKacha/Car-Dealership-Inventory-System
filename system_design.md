# System Design: Car Dealership Inventory System

> **Project:** Incubyte TDD Kata Assessment
> **Stack:** FastAPI (Python) + Vite/React/TypeScript + Tailwind CSS + PostgreSQL
> **Date:** 2026-07-22

---

## 1. Architecture Overview

```mermaid
graph TB
    subgraph Client["Frontend (Vite + React + TS)"]
        UI[React SPA]
        AX[Axios Interceptors]
        AC[AuthContext<br/>Access Token in Memory]
        RT[React Router]
    end

    subgraph Server["Backend (FastAPI + Uvicorn)"]
        FW[FastAPI App]
        RL[Rate Limiter<br/>slowapi 5/min/IP]
        CSP[CSP Headers Middleware]
        CORS[CORS Middleware]
        Routes["API Routes<br/>auth.py | vehicles.py"]
        Services["Service Layer<br/>auth_service | vehicle_service"]
        DB_ACCESS[Database Access<br/>SQLAlchemy ORM]
    end

    subgraph Storage["Persistence"]
        DB[(PostgreSQL Database<br/>car_dealership)]
        JWT[JWT Secret Key<br/>256-bit from .env]
    end

    subgraph Tokens["Token Flow"]
        AT[Access Token<br/>15 min · In-Memory]
        RT["Refresh Token<br/>7 days · httpOnly Secure<br/>SameSite=Lax Cookie"]
        CT["CSRF Token<br/>Non-httpOnly Cookie"]
    end

    UI --> AX
    AX -->|Auth Header: Bearer| FW
    AX -->|Auto-refresh on 401| FW
    FW --> RL --> CSP --> CORS --> Routes --> Services --> DB_ACCESS --> DB
    Services --> JWT
    AC --> AX
    RT -.->|Browser auto-sends| FW
```

### Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Backend Framework** | FastAPI | Async by default, auto OpenAPI docs, Pydantic validation built-in |
| **ORM** | SQLAlchemy 2.0 (sync) | Industry standard; sync mode is simpler and avoids async ORM complexity; FastAPI runs sync endpoints in a threadpool with no performance cost |
| **Database** | PostgreSQL | Production-grade RDBMS; proper `SELECT FOR UPDATE`, native DECIMAL type for prices, ENUM support for categories, strong concurrency |
| **Password Hashing** | Argon2id via passlib | OWASP #1 recommendation for new projects in 2025+; memory-hard (64MB), resistant to GPU/ASIC; RFC 9106 standardized; salt auto-embedded in output |
| **Auth Strategy** | Access token (15min, in-memory) + Refresh token (7 days, httpOnly Secure SameSite=Lax cookie, rotated every use) | Industry standard per Auth0, Okta, OWASP; refresh token rotation detects theft; CSRF structurally prevented for state-changing APIs |
| **Frontend Build** | Vite | Fastest DX, native ESM, great TypeScript support |
| **State Management** | React Context + useReducer | No external dependency; sufficient for this scope |
| **API Client** | Axios with interceptor | Auto-injects Bearer token; interceptor catches 401 → calls `/api/auth/refresh` → retries original request |
| **Testing** | pytest + httpx + pytest-cov | FastAPI's TestClient via httpx; coverage reporting |
| **Rate Limiting** | slowapi on login (5 attempts/min/IP) | Prevents brute-force and credential stuffing per OWASP ASVS |
| **Database Transactions** | SQLAlchemy atomic commits + `UPDATE...WHERE quantity > 0` for purchase | Prevents overselling even under concurrent requests |

---

## 2. Database Schema (ERD)

```mermaid
erDiagram
    User {
        int id PK
        string email UK
        string username UK
        string hashed_password "Argon2id hash"
        string role "user | admin"
        datetime created_at
        datetime updated_at
    }

    Vehicle {
        int id PK
        string make
        string model
        enum category "SUV | SEDAN | TRUCK | COUPE | HATCHBACK | VAN"
        decimal price "Numeric(10,2)"
        int quantity ">= 0"
        datetime created_at
        datetime updated_at
    }

    RefreshToken {
        int id PK
        int user_id FK
        string token_hash "SHA-256 of opaque token"
        uuid family_id "groups rotation chain"
        datetime expires_at
        boolean is_revoked
        datetime created_at
    }

    User ||--o{ Vehicle : "created_by"
    User ||--o{ RefreshToken : "has"
```

### User Model

```python
class User(Base):
    id: int              # Primary key, auto-increment
    email: str           # Unique, used for login
    username: str        # Unique, display name
    hashed_password: str # Argon2id hash (salt auto-embedded in hash string)
    role: str            # "user" or "admin"
    created_at: datetime # Auto-set on creation
    updated_at: datetime # Auto-updated
```

### RefreshToken Model

```python
class RefreshToken(Base):
    id: int              # Primary key
    user_id: int         # FK to users.id
    token_hash: str      # SHA-256 of the opaque refresh token string
    family_id: uuid      # UUID; shared across rotation chain — reuse detection
    expires_at: datetime # 7 days from issuance
    is_revoked: bool     # True if rotated out or logged out
    created_at: datetime # Auto-set
```

> **Why opaque tokens?** The refresh token stored in the cookie is a random 32-byte string (not a JWT). Only its SHA-256 hash is stored in the database. If the database is breached, refresh tokens cannot be forged or decrypted. This is the standard pattern used by Auth0 and Okta.

### Vehicle Model

```python
class Vehicle(Base):
    id: int              # Primary key, auto-increment
    make: str            # e.g. "Toyota", "Honda"
    model: str           # e.g. "Camry", "Civic"
    category: str        # Enum: SUV, SEDAN, TRUCK, COUPE, HATCHBACK, VAN
    price: Decimal       # SQLAlchemy Numeric(10,2) — precise to 2 decimal places
    quantity: int        # >= 0, checked before purchase atomically
    created_at: datetime
    updated_at: datetime
```

> **Price storage:** Using `Numeric(10,2)` via PostgreSQL's native DECIMAL type guarantees exact precision — unlike float, it won't have rounding errors. Internally it maps to Python `Decimal`.

---

## 3. API Endpoints

### Auth (Public)

| Method | Endpoint | Description | Request Body | Response |
|---|---|---|---|---|
| POST | `/api/auth/register` | Register new user | `{email, username, password, admin_key?}` | `{id, email, username, role}` |
| POST | `/api/auth/login` | Login, get tokens | `{email, password}` | **Body:** `{access_token (15min)}` **Set-Cookie:** `refresh_token` (httpOnly, Secure, SameSite=Lax, 7d) + `csrf_token` (non-httpOnly, SameSite=Lax) |
| POST | `/api/auth/refresh` | Refresh access token (reads `refresh_token` cookie, rotates it, checks `X-CSRF-Protection` header) | — | **Body:** `{access_token (15min)}` **Set-Cookie:** new `refresh_token` cookie |
| POST | `/api/auth/logout` | Revoke all refresh tokens for user (requires valid access token) | — | `204 No Content` |

> **Admin Key:** If `admin_key` matches the server's `ADMIN_SECRET_KEY` env var, the user is created with `role="admin"`. Otherwise `role="user"`.
>
> **Refresh Token Rotation:** Every call to `/api/auth/refresh` issues a new refresh token (same `family_id`) and revokes the previous one. If a revoked token is presented (reuse detected), the ENTIRE family is revoked — attacker is blocked, user is forced to re-login.
>
> **CSRF on Refresh:** The `/api/auth/refresh` endpoint requires a custom `X-CSRF-Protection: 1` header. The associated `csrf_token` non-httpOnly cookie enables the frontend to read and set this header. Cross-origin forms cannot set custom headers — preventing CSRF on the refresh flow.
>
> **Rate Limiting:** Login endpoint is rate-limited to 5 attempts per minute per IP via `slowapi`.

### Vehicles (Protected — requires JWT)

| Method | Endpoint | Description | Auth | Request Body / Params | Response |
|---|---|---|---|---|---|
| GET | `/api/vehicles` | List all vehicles | User | — | `Vehicle[]` |
| GET | `/api/vehicles/search` | Search vehicles | User | `?make=&model=&category=&price_min=&price_max=` | `Vehicle[]` |
| POST | `/api/vehicles` | Add vehicle | Admin | `{make, model, category, price, quantity}` | `Vehicle` |
| PUT | `/api/vehicles/{id}` | Update vehicle | Admin | `{make?, model?, ...}` | `Vehicle` |
| DELETE | `/api/vehicles/{id}` | Delete vehicle | Admin | — | `204 No Content` |
| POST | `/api/vehicles/{id}/purchase` | Purchase (decrease qty) | User | — | `Vehicle` |
| POST | `/api/vehicles/{id}/restock` | Restock (increase qty) | Admin | `{quantity: int}` | `Vehicle` |

### Auth Flow

```mermaid
sequenceDiagram
    participant C as Client (React)
    participant API as FastAPI
    participant DB as Database

    Note over C,API: REGISTRATION
    C->>API: POST /api/auth/register {email, password, username, admin_key?}
    API->>API: Validate input (Pydantic)
    API->>API: Check password against top-10000 weak list
    API->>DB: Check email uniqueness
    API->>API: Hash password (Argon2id, m=64MB, t=3, p=4)
    API->>API: Set role based on admin_key
    API->>DB: INSERT user
    API-->>C: 201 {id, email, username, role}
    Note over API: No tokens issued — user must log in

    Note over C,API: LOGIN
    C->>API: POST /api/auth/login {email, password}
    Note over API: Rate limited: 5/min/IP
    API->>DB: Fetch user by email
    API->>API: Verify password (Argon2id)
    API-->>C: 401 "Invalid email or password" if either fails
    API->>API: Generate access_token (JWT, 15 min, sub+role)
    API->>API: Generate opaque refresh_token (random 32 bytes)
    API->>API: SHA-256 hash → store in refresh_tokens table with family_id
    API-->>C: 200 {access_token}
    API-->>C: Set-Cookie: refresh_token (httpOnly, Secure, SameSite=Lax, 7d)
    API-->>C: Set-Cookie: csrf_token (non-httpOnly, SameSite=Lax)

    Note over C,API: AUTHENTICATED REQUEST
    C->>API: GET /api/vehicles (Authorization: Bearer <access_token>)
    API->>API: Decode & verify JWT signature + expiry
    API->>API: Inject current_user dependency
    API->>DB: Query vehicles
    API-->>C: 200 Vehicle[]

    Note over C,API: TOKEN REFRESH (triggered by 401 interceptor)
    C->>API: POST /api/auth/refresh
    Note over C: Axios interceptor catches 401
    Note over C: Reads csrf_token cookie → sets X-CSRF-Protection: 1 header
    Note over API: Browser auto-sends refresh_token cookie
    API->>API: Verify X-CSRF-Protection: 1 header present
    API->>API: Extract refresh_token from cookie
    API->>API: SHA-256 hash → lookup in refresh_tokens table
    API->>API: Check not revoked, not expired
    API->>API: ROTATE: revoke old token, issue new (same family_id)
    API-->>C: 200 {access_token (new, 15 min)}
    API-->>C: Set-Cookie: refresh_token (new, httpOnly, 7d)

    Note over C,API: REUSE DETECTION
    Note over API: If revoked token presented → revoke ALL tokens in family_id
    Note over API: Forced re-login for legitimate user

    Note over C,API: LOGOUT
    C->>API: POST /api/auth/logout (Authorization: Bearer <access_token>)
    API->>API: Revoke ALL refresh tokens for this user
    API-->>C: 204 No Content
    API-->>C: Clear-Cookie: refresh_token, csrf_token
```

### Search/Filter Logic

```
GET /api/vehicles/search?make=Toyota&category=SUV&price_min=20000&price_max=50000
```

- All query params are optional
- Filters are combined with AND
- `make` and `model` are case-insensitive partial matches (`ILIKE` / `LOWER LIKE`)
- `category` is exact match
- `price_min` and `price_max` are inclusive range filters
- If no params provided, returns all vehicles (same as GET /api/vehicles)

---

## 4. Project Structure

```
v1/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app factory, CORS, lifespan
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py         # /api/auth/*
│   │   │   │   └── vehicles.py     # /api/vehicles/*
│   │   │   └── deps.py             # Dependency injection (get_db, get_current_user, etc.)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # pydantic-settings (env vars, defaults)
│   │   │   ├── security.py         # JWT create/verify, password hash/verify
│   │   │   └── database.py         # SQLAlchemy engine, SessionLocal, Base
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User SQLAlchemy model
│   │   │   ├── vehicle.py          # Vehicle SQLAlchemy model
│   │   │   └── refresh_token.py    # RefreshToken SQLAlchemy model (opaque, hashed, family_id for rotation)
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # RegisterRequest, LoginRequest, TokenResponse, UserResponse
│   │   │   └── vehicle.py          # VehicleCreate, VehicleUpdate, VehicleResponse, VehicleSearchParams
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py     # Business logic: register, authenticate
│   │       └── vehicle_service.py  # Business logic: CRUD, purchase, restock, search
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # Fixtures: test client, test DB, auth headers
│   │   ├── test_auth.py            # Auth endpoint tests
│   │   └── test_vehicles.py        # Vehicle endpoint tests
│   │
│   ├── alembic/                    # (Optional — for production touch, but create_all is sufficient for SQLite)
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts           # Axios instance, interceptors, typed API functions
│   │   │
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   └── ThemeToggle.tsx  # Light/dark switch
│   │   │   ├── Layout.tsx           # Navbar + main + footer
│   │   │   ├── ProtectedRoute.tsx   # Redirect if not authenticated
│   │   │   └── AdminRoute.tsx       # Redirect if not admin
│   │   │
│   │   ├── context/
│   │   │   └── AuthContext.tsx       # Auth state + login/logout/register
│   │   │
│   │   ├── hooks/
│   │   │   └── useVehicles.ts       # Fetch, search, purchase vehicles
│   │   │
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx        # Vehicle grid + search + purchase
│   │   │   ├── Admin.tsx            # Add/edit/delete/restock vehicles
│   │   │   └── NotFound.tsx
│   │   │
│   │   ├── types/
│   │   │   └── index.ts             # Shared TypeScript interfaces
│   │   │
│   │   ├── App.tsx                  # Routes setup
│   │   └── main.tsx                 # Entry point
│   │
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── system_design.md                 # This file
├── PROMPTS.md                       # Full AI chat history
└── README.md                        # Project documentation
```

---

## 5. Frontend Component Tree & Routing

```mermaid
graph TB
    App --> Router
    Router --> Layout
    Layout --> Navbar
    Layout --> ThemeToggle
    Layout --> Content

    subgraph Content["Routes (React Router)"]
        direction TB
        Login["/login<br/>Login.tsx"]
        Register["/register<br/>Register.tsx"]
        Dashboard["/<br/>Dashboard.tsx"]
        Admin["/admin<br/>Admin.tsx"]
        NotFound["*<br/>NotFound.tsx"]
    end

    Dashboard --> VehicleGrid[Vehicle Cards Grid]
    Dashboard --> SearchBar[Search + Filter Bar]
    Dashboard --> PurchaseBtn[Purchase Button]

    Admin --> VehicleForm[Add/Edit Form]
    Admin --> VehicleTable[Vehicles Table]
    Admin --> RestockBtn[Restock Button]
    Admin --> DeleteBtn[Delete Button]

    Router --> ProtectedRoute
    ProtectedRoute --> Dashboard
    ProtectedRoute --> AdminRoute
    AdminRoute --> Admin
```

### Route Table

| Path | Component | Auth | Role |
|---|---|---|---|
| `/login` | Login.tsx | Public | — |
| `/register` | Register.tsx | Public | — |
| `/` | Dashboard.tsx | Protected | user/admin |
| `/admin` | Admin.tsx | Protected | admin only |
| `*` | NotFound.tsx | Public | — |

### Theme System

- CSS variables for colors, toggled via `class="dark"` on `<html>`
- Tailwind's `darkMode: 'class'` strategy
- `ThemeToggle` component: sun/moon icon button
- Theme preference persisted in `localStorage`

---

## 6. Error Handling Strategy

### Backend

```python
# Custom exception hierarchy
class AppException(Exception):      # Base
    pass

class NotFoundException(AppException):       # 404
    pass

class UnauthorizedException(AppException):   # 401
    pass

class ForbiddenException(AppException):      # 403
    pass

class ConflictException(AppException):       # 409
    pass

class ValidationException(AppException):     # 422
    pass
```

- Global exception handler registered in FastAPI
- All errors return consistent JSON shape: `{"detail": {"code": "ERROR_CODE", "message": "Human-readable"}}`
- Pydantic validation errors pass through FastAPI's default 422 handler

### Frontend

- Axios response interceptor catches 401 → auto-logout + redirect to `/login`
- Form validation happens both on frontend (HTML5 + custom) and backend (Pydantic)
- Error toasts for API failures

---

## 7. TDD Workflow & Git Strategy

### Commit Pattern (Red-Green-Refactor)

Each feature cycle produces 3 commits:

```
test: add auth register tests                           # RED — write failing tests
feat: implement user registration endpoint               # GREEN — make tests pass
refactor: extract password hashing into security module  # REFACTOR — clean up
```

### AI Co-Author Format

For every commit where AI assisted, add:

```
Co-authored-by: Qwen Code <AI@users.noreply.github.com>
```

### Commit Sequence Plan

```
1. chore: initialize backend project structure
2. chore: initialize frontend project with Vite + React + Tailwind
   (Setup commits — no AI co-author needed)

--- Auth Module ---
3. test: add auth register and login tests
4. feat: implement auth register and login endpoints
5. refactor: extract security utilities into core module

--- Vehicles Module ---
6. test: add vehicle CRUD and inventory tests
7. feat: implement vehicle endpoints (CRUD + purchase + restock)
8. refactor: clean up vehicle service layer

--- Frontend ---
9. feat: add auth pages (login/register) with AuthContext
10. feat: add vehicle dashboard with search and purchase
11. feat: add admin panel with vehicle management
12. style: polish UI, responsive design, animations

--- Documentation ---
13. docs: add README with setup instructions and screenshots
14. docs: add PROMPTS.md with complete AI chat history
```

---

## 8. Testing Strategy

### Backend Tests (pytest + httpx)

```python
# conftest.py fixtures:
# - test_db: Creates a test database + tables, drops after tests
# - test_client: FastAPI TestClient bound to test_db
# - db_session: Each test wrapped in a transaction that auto-rolls back
# - user_token: JWT for regular user
# - admin_token: JWT for admin user
# - user_headers: {Authorization: Bearer <user_token>}
# - admin_headers: {Authorization: Bearer <admin_token>}
```

**Test cases:**

| Test File | Test Case | Verifies |
|---|---|---|
| `test_auth.py` | `test_register_success` | 201 + user data |
| | `test_register_duplicate_email` | 409 conflict |
| | `test_register_admin_with_key` | 201 + role=admin |
| | `test_register_invalid_email` | 422 validation |
| | `test_login_success` | 200 + valid JWT |
| | `test_login_wrong_password` | 401 unauthorized |
| | `test_login_nonexistent_user` | 401 unauthorized |
| `test_vehicles.py` | `test_create_vehicle_as_admin` | 201 + vehicle data |
| | `test_create_vehicle_as_user` | 403 forbidden |
| | `test_create_vehicle_unauthenticated` | 401 unauthorized |
| | `test_list_vehicles` | 200 + paginated list |
| | `test_search_vehicles_by_make` | 200 + filtered results |
| | `test_search_vehicles_by_price_range` | 200 + filtered results |
| | `test_search_vehicles_no_params` | 200 + all vehicles |
| | `test_update_vehicle_as_admin` | 200 + updated data |
| | `test_update_vehicle_as_user` | 403 forbidden |
| | `test_delete_vehicle_as_admin` | 204 no content |
| | `test_purchase_vehicle_success` | 200 + decreased quantity |
| | `test_purchase_vehicle_zero_quantity` | 400 out of stock |
| | `test_restock_vehicle_as_admin` | 200 + increased quantity |
| | `test_restock_vehicle_as_user` | 403 forbidden |

### Frontend Tests (Vitest + React Testing Library)

Placeholder: Frontend testing is recommended but not strictly required by the spec. Focus will be on component-level tests for critical flows (auth, purchase).

---

## 9. Design System (UI)

### Color Palette

| Token | Light | Dark |
|---|---|---|
| `--bg-primary` | `#FFFFFF` | `#0F172A` (slate-900) |
| `--bg-secondary` | `#F8FAFC` (slate-50) | `#1E293B` (slate-800) |
| `--bg-card` | `#FFFFFF` | `#1E293B` |
| `--text-primary` | `#0F172A` | `#F1F5F9` |
| `--text-secondary` | `#64748B` | `#94A3B8` |
| `--accent` | `#2563EB` (blue-600) | `#3B82F6` (blue-500) |
| `--accent-hover` | `#1D4ED8` | `#60A5FA` |
| `--success` | `#16A34A` (green-600) | `#22C55E` (green-500) |
| `--danger` | `#DC2626` (red-600) | `#EF4444` (red-500) |
| `--border` | `#E2E8F0` (slate-200) | `#334155` (slate-700) |

### Typography

- **Font:** Inter (system sans-serif fallback)
- **Headings:** Semi-bold, clean hierarchy
- **Body:** Regular 400, good line-height for readability

### Components

All UI components to be hand-crafted (no headless UI library) to ensure unique, non-template look:
- **Cards** with subtle border and hover elevation
- **Buttons** with smooth transitions
- **Inputs** with focus ring and floating labels
- **Badge** for vehicle category tags
- **Modal** for admin forms
- **Glass navbar** with backdrop blur

---

## 10. Security Architecture

This project implements OWASP ASVS-compliant security for authentication, authorization, token management, and data protection. Below is the full layered defense.

### 10.1 Password Storage (Argon2id)

**Algorithm:** Argon2id — OWASP #1 recommendation for new projects (2025+). RFC 9106 standardized, winner of the Password Hashing Competition.

**Parameters:**
```
Memory cost:   64 MB (65,536 KiB)   — memory-hard, resists GPU/ASIC
Time cost:     3 iterations          — ~100ms verification on modern CPU
Parallelism:   1                     — single-threaded is sufficient
Salt:          128-bit (16 bytes)    — auto-generated, auto-embedded in output
```

**Implementation:**
```python
from passlib.hash import argon2

# Hashing — salt is automatic, embedded in the output string
hashed = argon2.using(timecost=3, memorycost=65536, parallelism=4).hash(password)
# Save `hashed` directly to DB. Output includes algorithm, params, salt, and hash.

# Verification — library extracts salt from stored hash automatically
is_valid = argon2.verify(password, stored_hash)
```

**Why not bcrypt?** bcrypt is still cryptographically sound (cost ≥ 12) but has a fixed 4 KB memory footprint — modern GPUs can parallelize thousands of bcrypt checks. Argon2id's 64 MB memory cost makes GPU/ASIC attacks exponentially more expensive.

### 10.2 Token Architecture

```
                    ┌──────────────────────────────────────────────────┐
                    │              POST /api/auth/login                │
                    └──────────────────────┬───────────────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              ▼                            ▼                            ▼
     ┌──────────────────┐     ┌──────────────────────────┐     ┌──────────────────┐
     │   Access Token   │     │     Refresh Token        │     │   CSRF Token     │
     │                  │     │                          │     │                  │
     │ Format: JWT      │     │ Format: Opaque 32 bytes  │     │ Format: Random   │
     │ Algorithm: HS256 │     │ Storage: SHA-256 in DB   │     │                   │
     │ Expiry: 15 min   │     │ Expiry: 7 days           │     │ Cookie: non-     │
     │ Storage: React   │     │ Cookie: httpOnly Secure  │     │   httpOnly       │
     │   memory/context │     │   SameSite=Lax           │     │   SameSite=Lax   │
     │ Payload: sub,    │     │ Rotation: Every refresh  │     │ Purpose: CSRF    │
     │   role           │     │ Reuse: Revokes family    │     │   header check   │
     └──────────────────┘     └──────────────────────────┘     └──────────────────┘
```

| Token | Expiry | Storage | Why This Way |
|---|---|---|---|
| **Access** | 15 min | React in-memory (Context) | Never persisted to disk; lost on page close → limits exposure window |
| **Refresh** | 7 days | httpOnly Secure SameSite=Lax cookie | JS can't read it → immune to XSS; browser auto-sends on refresh endpoint |
| **CSRF** | 7 days | Non-httpOnly SameSite=Lax cookie | JS reads it to set `X-CSRF-Protection` header; cross-origin forms can't set custom headers |

### 10.3 Refresh Token Rotation & Reuse Detection

```
LOGIN:
  family_id = uuid4()
  refresh_token = secrets.token_urlsafe(32)
  Store: SHA256(refresh_token), family_id, user_id, expires_at=7d
  → Set-Cookie: refresh_token (httpOnly, Secure, SameSite=Lax)

REFRESH (normal):
  1. Receive refresh_token from cookie
  2. SHA256(token) → lookup in DB
  3. Verify: not revoked, not expired
  4. Generate NEW refresh_token (same family_id)
  5. REVOKE old token in DB (is_revoked = True)
  6. Store new: SHA256(new_token), same family_id
  7. → Set-Cookie: refresh_token (new)
  8. → Return new access_token

REUSE DETECTED (attacker stole token and used it AFTER rotation):
  1. Receive refresh_token from cookie
  2. SHA256(token) → lookup in DB → found but is_revoked = True
  3. Means: someone used this token after it was rotated
  4. → Revoke ALL tokens with this family_id
  5. → User is forced to re-login on next request
  6. → Attacker's refresh attempt fails
```

This is the same pattern Auth0 and Okta use. An attacker who steals the refresh token gets **one** use before rotation invalidates it. The legitimate user's next request fails → they re-login → attacker is locked out.

### 10.4 CSRF Protection

**Why CSRF is needed:** Refresh tokens are stored in cookies (auto-sent by browser). Without CSRF protection, an attacker's site could trigger `POST /api/auth/refresh` via a hidden form.

**How we prevent it:**

```
Refresh endpoint requires BOTH:
  1. refresh_token cookie (httpOnly, browser-sent)
  2. X-CSRF-Protection: 1 custom header

Browser security:
  - Cross-origin JavaScript cannot set custom headers (preflighted CORS)
  - SameSite=Lax prevents cookie from being sent on cross-origin POSTs
  - The csrf_token cookie (non-httpOnly, SameSite=Lax) is sent on same-origin
    requests → frontend reads it, sets the header

Therefore: Only same-origin JavaScript can successfully call /api/auth/refresh.
State-changing endpoints (purchase, restock, delete) use Authorization: Bearer
header → CSRF is structurally impossible for those.
```

### 10.5 Rate Limiting

| Endpoint | Limit | Tool |
|---|---|---|
| `POST /api/auth/login` | 5 attempts / minute / IP | slowapi |
| `POST /api/auth/register` | 3 registrations / hour / IP | slowapi |
| All other endpoints | No limit (authenticated + parameterized) | — |

### 10.6 Authorization (Two-Layer RBAC)

Every protected endpoint enforces authorization at **two independent layers**:

```python
# LAYER 1: Route dependency (FastAPI Depends)
@app.post("/api/vehicles", dependencies=[Depends(require_admin)])
def create_vehicle(...): ...

# LAYER 2: Service layer (double-check)
def delete_vehicle(db: Session, vehicle_id: int, current_user: User):
    if current_user.role != "admin":
        raise ForbiddenException("Only admins can delete vehicles")
    vehicle = get_vehicle_or_404(db, vehicle_id)
    db.delete(vehicle)
```

| Role | Permissions |
|---|---|
| **admin** | All: CRUD vehicles, purchase, restock |
| **user** | View vehicles, search, purchase |
| **unauthenticated** | Register, login only |

### 10.7 Content Security Policy (CSP)

```python
# FastAPI middleware
@app.middleware("http")
async def add_csp_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "  # Required for React/Tailwind
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self' http://localhost:5173"
    )
    return response
```

### 10.8 Input & Output Protection

| Threat | Defense | OWASP Category |
|---|---|---|
| **SQL Injection** | SQLAlchemy parameterized queries — zero raw SQL strings | A03:2021 Injection |
| **Mass Assignment** | Pydantic schemas whitelist fields — no `**request.body` pass-through | API8:2019 |
| **IDOR** | All operations check existence + return generic 404 | A01:2021 BOLA |
| **Error Leakage** | No stack traces; generic error messages; debug=False in production | A04:2021 |
| **Email Enumeration** | Same `"Invalid email or password"` for all login failures | A07:2025 |
| **XSS** | React auto-escapes JSX; CSP restricts script sources; no `dangerouslySetInnerHTML` | A03:2021 |
| **CSRF (state-changing)** | Structurally prevented — JWT in Authorization header, NOT cookies | A01:2021 |

### 10.9 Frontend Token Handling

```typescript
// AuthContext.tsx — access token lives ONLY in React state
interface AuthState {
  accessToken: string | null;     // NEVER written to localStorage
  user: User | null;
  isAuthenticated: boolean;
}

// Axios interceptor — auto-injects token, auto-refreshes
api.interceptors.request.use((config) => {
  config.headers.Authorization = `Bearer ${getAccessToken()}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      // Sets X-CSRF-Protection header (reads csrf_token cookie)
      // Browser auto-sends refresh_token cookie
      const { access_token } = await refreshTokens();
      setAccessToken(access_token);
      error.config.headers.Authorization = `Bearer ${access_token}`;
      return api(error.config);  // Retry original request
    }
    return Promise.reject(error);
  }
);
```

### 10.10 Environment & Secrets Management

```
backend/
├── .env                          # LOCAL ONLY — never committed
├── .env.example                  # Committed — placeholder values
└── .gitignore                    # Excludes .env, __pycache__, node_modules/
```

```bash
# .env.example (committed template)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/car_dealership
JWT_SECRET_KEY=your-256-bit-secret-min-32-chars-change-in-production
ADMIN_SECRET_KEY=your-admin-secret-min-32-chars
```

```bash
# .gitignore
.env
__pycache__/
*.pyc
node_modules/
dist/
.vite/
```

### 10.11 CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,                    # Required for cookies
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Protection"],
)
```

### 10.12 SQLAlchemy Session Hygiene

```python
# FastAPI dependency — guaranteed cleanup
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()    # Always runs — even on exception

# Tests use transaction-per-test with rollback
# No data leakage between tests
```

### 10.13 Security Summary

| Area | Standard | Implementation |
|---|---|---|
| **Password Hashing** | OWASP #1: Argon2id | passlib, m=64MB, t=3, p=4, salt auto-embedded |
| **Access Token** | JWT, 15 min, in-memory | HS256, sub+role payload, never persisted |
| **Refresh Token** | Opaque, 7 days, httpOnly cookie | Random 32 bytes, SHA-256 in DB, rotated each use |
| **Rotation** | Every refresh + reuse detection | Family tracking; revoked family on reuse |
| **CSRF** | Custom header + SameSite=Lax | X-CSRF-Protection required on refresh endpoint |
| **Rate Limiting** | 5 login attempts/min/IP | slowapi on auth endpoints |
| **Authorization** | Two-layer RBAC | Route Depends + service verification |
| **CSP** | Restrict script/style sources | FastAPI middleware |
| **Injection** | Parameterized queries | SQLAlchemy ORM, zero raw SQL |
| **Error Handling** | No information leak | Generic messages, no stack traces |
| **Secrets** | Env isolation | .env (gitignored) + .env.example (committed) |

---

## 11. Deliverables Checklist

- [x] Backend REST API (FastAPI + SQLAlchemy + PostgreSQL)
- [x] JWT authentication with access + refresh token pattern
- [x] Refresh token rotation + reuse detection (family tracking)
- [x] CSRF protection on refresh endpoint (custom header + SameSite=Lax)
- [x] Argon2id password hashing (OWASP #1 standard)
- [x] Rate limiting on auth endpoints (slowapi, 5/min/IP)
- [x] CSP headers via FastAPI middleware
- [x] Two-layer RBAC authorization (route + service)
- [x] Vehicle CRUD (admin-only create/update/delete)
- [x] Vehicle search/filter (make, model, category, price range)
- [x] Purchase (atomic `UPDATE...WHERE quantity > 0`, prevents overselling)
- [x] Restock (admin-only, increase quantity)
- [x] Frontend SPA (React + Tailwind + light/dark theme)
- [x] Auth pages (login + register)
- [x] Dashboard (vehicle list, search, purchase)
- [x] Admin panel (add/edit/delete, restock)
- [x] TDD commit history (red-green-refactor)
- [x] AI co-author attributions
- [x] README.md (setup, screenshots, AI usage, test report)
- [x] PROMPTS.md (full AI chat history)

---

## 12. Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-22 | FastAPI over Django | Async, auto-docs, simpler TDD setup |
| 2026-07-22 | PostgreSQL over SQLite | Production-grade DB; proper concurrency control, DECIMAL type, ENUM support; PostgreSQL available locally |
| 2026-07-22 | Sync SQLAlchemy | Simpler test setup with PostgreSQL; FastAPI threads sync endpoints in a threadpool |
| 2026-07-22 | Admin via secret key | Clean UX — no seed scripts needed |
| 2026-07-22 | Fixed vehicle categories | Cleaner data, better filter UX |
| 2026-07-22 | React Context over Redux/Zustand | Sufficient for scope, no extra dependency |
| 2026-07-22 | Light/dark theme via Tailwind class strategy | CSS variables + class toggle, localStorage persistent |
| 2026-07-22 | Price as Decimal/Numeric(10,2) | PostgreSQL's native DECIMAL avoids float precision issues |
| 2026-07-22 | Purchase uses `UPDATE...WHERE quantity > 0` returning | Single atomic SQL statement prevents overselling |
| 2026-07-22 | Argon2id over bcrypt | OWASP #1 recommendation (2025+); memory-hard (64 MB) resists GPU/ASIC |
| 2026-07-22 | Access token in-memory (15 min) + refresh token httpOnly cookie (7 days) | Industry standard per Auth0, Okta, OWASP; refresh rotation detects theft |
| 2026-07-22 | CSRF protection on refresh endpoint | Required because refresh tokens use cookies; double-submit header pattern |
| 2026-07-22 | Rate limiting via slowapi | Prevents brute-force credential stuffing per OWASP ASVS |
| 2026-07-22 | CSP headers via middleware | Defense-in-depth against XSS even with React escaping |
