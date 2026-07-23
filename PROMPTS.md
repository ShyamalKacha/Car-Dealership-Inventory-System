# AI Prompts & Responses

**AI Tool Used:** Qwen Code CLI Agent

---

## 1. System Design & Architecture

**Prompt:**
> I'm starting a full-stack Car Dealership Inventory System as a technical assessment. The stack needs to be Python/FastAPI for the backend and React/Tailwind for the frontend with PostgreSQL. The requirements include JWT authentication, vehicle CRUD, inventory management (purchase/restock), admin roles, and TDD with red-green-refactor commits. I need to plan the architecture before writing any code. What should the system design look like?

**Response:**
Recommended FastAPI + SQLAlchemy 2.0 + PostgreSQL on the backend, Vite + React + Tailwind on the frontend. Proposed a layered architecture with routes → services → models separation, JWT access+refresh token pattern, and a test strategy using pytest + httpx with a separate test database.

**Prompt:**
> Let's think about security for this project. Walk me through the threats: SQL injection, XSS, CSRF, IDOR, rate limiting — which ones are actually relevant here given our JWT-in-header auth model?

**Response:**
Explained that SQL injection is prevented by SQLAlchemy ORM, CSRF is structurally impossible with Bearer tokens (not cookies) for state-changing endpoints, and XSS is mitigated by React's default JSX escaping. Identified token theft via XSS and login brute-forcing as the realistic threats.

**Prompt:**
> What does the industry standard look like for SPA authentication in production? I want to know what Auth0, Okta, and OWASP recommend — not the simplified approach.

**Response:**
Researched and presented the gold-standard pattern: Argon2id for password hashing (OWASP #1), in-memory access tokens with 15-minute expiry, opaque refresh tokens in httpOnly Secure SameSite cookies with rotation and reuse detection, CSRF protection via double-submit cookie on the refresh endpoint, and rate limiting on auth endpoints.

**Decision:** Adopted the full production pattern — Argon2id, access+refresh token architecture with rotation, CSRF protection, and rate limiting.

---

## 2. Backend Implementation

**Prompt:**
> I've designed the authentication module — register, login, refresh token rotation, and logout. The service layer should handle Argon2id password hashing, JWT generation, opaque refresh tokens with SHA-256 hashing, and family-based reuse detection. Can you generate the service and route implementations following this design?

**Response:**
Generated `auth_service.py` with `register()`, `authenticate()`, `create_refresh_token()`, `rotate_refresh_token()` (with reuse detection), and `revoke_all_user_tokens()`. Generated routes with proper cookie handling (httpOnly refresh token, non-httpOnly CSRF token, secure flag from config).

**Prompt:**
> Now I need the vehicle service layer — CRUD operations and inventory management. The purchase endpoint needs to be atomic to prevent overselling under concurrent requests. I'm thinking a single UPDATE ... WHERE quantity > 0 RETURNING statement should handle this. Generate the service and routes.

**Response:**
Generated `vehicle_service.py` with atomic purchase using SQLAlchemy's `update().where(quantity > 0).returning()`, plus create, list, search (by make, model, category, price range), update, delete, and restock. Routes enforce admin-only for create/update/delete/restock via two-layer authorization (route dependency + service check).

**Prompt:**
> I'm debugging a CORS preflight issue. The `OPTIONS /api/auth/refresh` request returns 400 while all other endpoints work fine. I suspect slowapi's auto-registered ASGI middleware is intercepting OPTIONS before the CORS middleware can respond. What's the cleanest fix here?

**Response:**
Diagnosed that slowapi's ASGI-level middleware wraps around Starlette middleware, intercepting OPTIONS preflight and returning 400 before CORS can reply. Recommended replacing slowapi with a custom in-memory sliding-window rate limiter that has zero ASGI middleware overhead, and using Starlette's `allow_origin_regex` in CORSMiddleware to handle dynamic localhost ports.

**Decision:** Removed slowapi entirely, implemented a 40-line custom rate limiter. CORS now uses `allow_origin_regex` to accept any localhost port.

**Prompt:**
> The frontend refresh-on-reload should work without redirecting to login. The access token lives in React state (lost on refresh), so the auth flow should call /api/auth/refresh on mount using the httpOnly cookie. Set up the AuthContext with axios interceptors for automatic token injection and 401 refresh.

**Response:**
Generated `AuthContext.tsx` with in-memory access token, axios request interceptor (injects Bearer token via ref), response interceptor (catches 401, calls refresh, retries original request), and `refreshTokens()` with promise deduplication.

---

## 3. Frontend Development

**Prompt:**
> I need the login and register pages with form validation, error handling, and a clean UI. The login should check the user's role and redirect admin users to the admin panel and regular users to the dashboard. Use the custom Button and Input components.

**Response:**
Generated `Login.tsx` and `Register.tsx` with email/password validation, error state display, loading states, and role-based post-login redirect.

**Prompt:**
> The dashboard needs a vehicle card grid with search/filter by make, model, category, and price range. Each card should show the vehicle details with a Purchase button that's disabled when quantity is zero. Add a loading skeleton state, empty state, and toast notification on successful purchase.

**Response:**
Generated `Dashboard.tsx` with skeleton loading cards, search form, vehicle card grid, purchase flow with toast notifications, and empty state with icon. Purchase button is hidden for admin users.

**Prompt:**
> The current UI uses the default Tailwind blue color palette which looks generic. I want a more sophisticated look — a warm cream background with teal as the accent color, and in dark mode a deep charcoal with vibrant teal. The design should feel professional and not template-like. Also add smooth page transitions and loading animations.

**Response:**
Redesigned the CSS variables from the default slate/blue to a custom warm + teal palette. Added `fade-in`, `slide-up`, and `scale-in` animations. Updated card hover effects, button transitions, and modal animations.

---

## 4. Testing

**Prompt:**
> I've designed the auth tests — registration (success, duplicate email, admin key, weak passwords, invalid email) and login (valid credentials, wrong password, nonexistent user, empty fields). The tests should use pytest with a test PostgreSQL database isolated per test session. Generate the test fixtures and test cases.

**Response:**
Generated `conftest.py` with session-scoped engine, per-test table cleanup, test client with overridden DB dependency, and user/admin token fixtures. Generated `test_auth.py` with all 12 test cases.

**Prompt:**
> Now I need the vehicle tests — create (admin, user, unauthenticated, invalid data), list, search (by make, model, category, price range, combined, no results), update, delete, purchase (success, out of stock, not found), and restock (admin, user, not found, invalid quantity). Generate the test file.

**Response:**
Generated `test_vehicles.py` with 26 test cases covering all vehicle and inventory endpoints.

---

## 5. Design & Polish

**Prompt:**
> The admin login currently redirects to the dashboard with a Purchase button, which doesn't make sense. Admin should go to the management panel on login, and the Purchase button should be hidden for admin users. The logo link should also respect this routing.

**Response:**
Updated login redirect logic, Layout logo link to route admin to `/admin`, and Dashboard to conditionally hide the Purchase button for admin users. Added a search/filter bar to the Admin page for vehicle management.

**Prompt:**
> I want to refine the color palette again — the current implementation still feels like it has generic tones. Let's use a warm cream background (#f5f2eb) with a deep teal accent (#0d9488) for light mode, and a rich dark charcoal (#0e0e12) with a brighter teal for dark mode. The borders should be warm beige, not gray.

**Response:**
Updated all CSS variables with the specified hex values, added accent-light variants for badges and hover states, and adjusted component styles to match the new palette.
