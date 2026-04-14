## CineQuest Backend — Technical Report (Phase VII)

### a) Bug Analysis (root cause + fix)

- **Auth/login failing with different username casing**
  - **Root cause**: Django usernames are case-sensitive; logging in with a different case than the stored username can fail.
  - **Fix**: Implemented a **custom SimpleJWT token serializer** that maps the login username using `username__iexact` to the stored username before authentication. Wired the token endpoint to a custom token view.
  - **Files**: `backend/users/serializers.py`, `backend/users/views.py`, `backend/cinequest/urls.py`
  - **Result**: Login is case-insensitive (any casing maps to the stored username). Registration also enforces case-insensitive uniqueness, so `Shira` and `shira` cannot both be created.
  
- **User registration validation gaps / inconsistent rules**
  - **Root cause**: Registration rules were incomplete for the exam requirements and could allow weak/invalid input.
  - **Fix**: Strengthened `RegisterSerializer`:
    - required `password_confirm` match
    - enforced Django’s `validate_password`
    - added extra project rules: **password must start with a capital letter** and **include at least one special character**
    - validated email format with a TLD using regex
    - normalized emails with `strip().lower()`
  - **Files**: `backend/users/serializers.py`
  - **Result**: Signups fail fast with clear 400 validation errors when invalid.

- **CORS failures during local development (frontend port switching)**
  - **Root cause**: Next.js dev server may run on `3001` when `3000` is occupied; backend CORS defaults did not allow `3001`.
  - **Fix**: Expanded allowed dev origins to include `localhost:3000/3001` and `127.0.0.1:3000/3001`.
  - **Files**: `backend/cinequest/settings.py`, `backend/.env.example`
  - **Result**: Browser calls succeed regardless of whether frontend is on port 3000 or 3001.

- **Environment variable naming mismatch**
  - **Root cause**: `.env.example` used `SECRET_KEY`, while settings read `DJANGO_SECRET_KEY`, causing confusing setup and accidental fallback keys.
  - **Fix**: Aligned `.env.example` with the real settings variable name and updated CORS sample values.
  - **Files**: `backend/.env.example`
  - **Result**: Setup instructions match runtime behavior.

- **Backend stability / maintainability issue: overly long dashboard endpoint**
  - **Root cause**: `dashboard_stats` combined aggregation, mapping, timeline building, and preference scoring in one long function.
  - **Fix**: Refactored into small helper functions while preserving the response shape:
    - `_parse_page`
    - `_build_genre_distribution`
    - `_build_activity_timeline`
    - `_build_preference_scores`
  - **Files**: `backend/recommendations/views.py`
  - **Result**: Cleaner logic, easier to review and modify without introducing regressions.

### b) Refactoring Decisions (what changed + why)

- **Refactored `dashboard_stats` to helper functions**
  - **Why**: Reduced duplication, improved readability, and separated responsibilities (parsing, aggregation, formatting).
  - **Impact**: No API contract changes; safer future maintenance.

### c) Architecture Changes (structural modifications)

- **Customized JWT token endpoint behavior**
  - Introduced `CustomTokenObtainPairSerializer` + `CustomTokenObtainPairView` and routed `/api/auth/token/` through it.
  - This is a small but meaningful auth-layer architecture change enabling case-insensitive login without altering the user model.

### d) Innovation Design (unique backend feature)

- **Custom password policy enforced at the API boundary**
  - **Problem solved**: Prevents weak/inconsistent passwords across any client (web/mobile/Postman).
  - **Rules added** (in addition to Django validators):
    - first character must be **uppercase**
    - must contain **≥1 special character**
  - **Where implemented**: `backend/users/serializers.py` in `RegisterSerializer.validate()`

### e) Testing Evidence (what was tested + results)

- **Migration/health**
  - `python manage.py check` → no issues
  - `python manage.py showmigrations --plan` → migrations applied (including user email constraint migration)

- **Automated tests**
  - `python manage.py test users` → PASS
  - `python manage.py test users recommendations movies` → PASS (49 tests)
  - Note: warnings like “Unauthorized”/“Bad Request” appear during tests because negative test cases intentionally validate 401/400 responses.

### f) Remaining Limitations (known risks / technical debt)

- **External dependency behavior**: TMDB failures now surface more clearly, but further work could standardise 502/503 responses across *all* endpoints that call TMDB.
- **DB config**: `DATABASE_URL` is supported, but local development still defaults to SQLite; production hardening (e.g., strict env requirements, per-env settings) would still be needed for deployment.

### Limitations addressed during development (closed)

- **Mixed auth modes**: removed SessionAuthentication to avoid CSRF/session confusion in a JWT SPA.
- **GET that mutates DB**: stopped persisting Wikipedia fields during a GET request; endpoint now returns enrichment data without writes.

## Backend Change Log (quick list)

- **Auth**
  - Case-insensitive JWT login via custom token serializer/view and URL wiring.
- **Users**
  - Strict registration validation (email TLD regex, password confirmation, Django validators + custom password rules).
  - Email normalization (`strip().lower()`).
- **Dev config**
  - `.env.example` aligned to actual variables; dev CORS origins updated for ports 3000/3001.
- **Refactor**
  - `dashboard_stats` refactored into helpers for maintainability.

