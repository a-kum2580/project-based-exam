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
  - `python manage.py test movies` after adaptive scan refactor → PASS (23 tests)
  - Note: warnings like “Unauthorized”/“Bad Request” appear during tests because negative test cases intentionally validate 401/400 responses.

### f) Remaining Limitations (known risks / technical debt)

- **External dependency behavior**: TMDB failures now surface more clearly, but further work could standardise 502/503 responses across *all* endpoints that call TMDB.
- **DB config**: `DATABASE_URL` is supported, but local development still defaults to SQLite; production hardening (e.g., strict env requirements, per-env settings) would still be needed for deployment.

### g) Code Smells & Technical Debt (28 identified issues)

#### **HIGH SEVERITY** (affects correctness/security/performance)

1. **Giant Function: `discover_filtered` (~150 lines)**
   - **Location**: `backend/movies/views.py:350-490`
   - **Issue**: Combines multiple responsibilities—parameter extraction, caching strategy, search filtering, pagination, and sorting—in one function.
   - **Impact**: Difficult to test individual logic, high regression risk on modifications.
   - **Fix Strategy**: Extract into `MovieDiscoveryService` class with separate methods for filtering, caching, and pagination.

   `MovieDiscoveryService` now divides responsibilities into focused methods:

      1. `parse_request_filters(query_params)`
        - Normalizes and validates request inputs into one filter dictionary.
        - Centralizes type-safe parsing for `page`, `year_from`, `year_to`, `rating_min`, `runtime_min`, `runtime_max`.

      2. `discover(filters)`
        - Entry point deciding between two branches:
          - query-aware branch (`_discover_with_query`) when `q` is present
          - discover API branch (`_discover_without_query`) when `q` is absent

      3. `_discover_with_query(filters)`
        - Builds cache payload from filter options.
        - Reads/writes cached filtered results.
        - Fetches and aggregates TMDB search pages when cache miss occurs.
        - Delegates filtering to `_apply_search_filters` and sorting to `_sort_movies`.
        - Performs final pagination and returns structured payload.

      4. `_discover_without_query(filters)`
        - Builds TMDB discover API params from filters.
        - Calls TMDB discover endpoint directly.
        - Returns normalized response payload (results/total/pages).

      5. `_apply_search_filters(all_results, filters)`
        - Applies in-memory filters in one place:
          - genre match
          - year range
          - minimum rating
          - language
          - optional runtime constraints (with runtime lookups)

      6. `_sort_movies(movies, sort)`
        - Encapsulates sorting strategy map and ordering rules.

      7. Internal helpers
        - `_safe_int` / `_safe_float`: consistent numeric parsing
        - `_ensure_tmdb_ok`: consistent TMDB error propagation (`APIException`)
        - `_build_cache_key`: deterministic cache key from sorted serialized payload

      #### View-layer changes made

      `discover_filtered` in `backend/movies/views.py` now has a narrow role:
      - sync service TMDB client reference
      - parse filters via service
      - call service discovery entry point
      - serialize TMDB movie list
      - return final response

      This reduced the endpoint from a large, multi-concern block to a compact orchestrator while keeping external API behavior and response keys intact.

      #### Why this is safer long-term

      - **Lower change risk**: modifications to filtering, sorting, or caching can be done in isolated methods.
      - **Better testability**: each method can be tested independently with focused fixtures/mocks.
      - **Clear ownership**: views manage HTTP lifecycle; service manages discovery domain logic.
      - **Easier extension**: adding new filters now involves extending parser + filter method rather than editing one very long function.

2. **Linear Scan of 500 TMDB Pages**
   - **Location**: `backend/movies/services/discovery_service.py` (`_discover_with_query`)
   - **Issue**: `discover_filtered` scans up to 500 pages sequentially for search results (~10,000 movies).
   - **Impact**: Response time could exceed 30+ seconds; API throttling/rate limit risks.
   - **Alternative Solution Implemented**: Adaptive early-stop scanning (not fixed hard cap).

   **What changed in code**
   - Added adaptive controls in `MovieDiscoveryService.__init__`:
     - `result_buffer_multiplier` (default `2.0`)
     - `max_consecutive_empty_pages` (default `3`)
   - Reworked `_discover_with_query` to stop scanning when either condition is met:
     1. enough filtered results collected for requested page (with buffer), or
     2. too many consecutive pages produce no filtered matches.
   - Added helper methods:
     - `_target_result_count(requested_page, page_size)`
     - `_should_stop_scan(current_count, target_count, empty_pages)`

   **Function division for this solution**
   - `_target_result_count`: computes dynamic target based on requested page and page size.
   - `_should_stop_scan`: centralizes stop decisions (target reached / empty-page threshold).
   - `_apply_search_filters`: still owns filtering logic but now works page-by-page.
   - `_sort_movies`: applied after adaptive accumulation to preserve output ordering contract.

   **Why this is better than a fixed 5-page cap**
   - Avoids truncating relevant results just because they are beyond an arbitrary page number.
   - Stops earlier when enough quality matches are already found.
   - Limits wasted calls when pages stop yielding usable results.
   - Maintains latency control while improving recall quality versus strict caps.

   **Verification**
   - Added targeted tests in `backend/movies/tests.py`:
     - `test_scan_stops_when_target_results_reached`
     - `test_scan_stops_after_consecutive_empty_filtered_pages`
   - `python manage.py test movies` passes with these cases included.

3. **GET Endpoint That Mutates Database**
   - **Location**: `backend/movies/views.py:122-135` (`PersonViewSet.enrich`)
   - **Issue**: `@action(detail=True, methods=["get"])` performs `.save()` on the person model.
   - **Impact**: Violates REST principles; idempotent GET requests should not have side effects.
   - **Fix Strategy**: Convert to POST endpoint or make enrichment on-demand without persistence.

4. **Missing Pagination Boundary Checks**
   - **Location**: Throughout views (especially `discover_filtered`)
   - **Issue**: `page` parameter not validated for negative values or absurd ranges (e.g., `?page=-999` or `?page=99999`).
   - **Impact**: Invalid queries could bypass caching or cause unexpected API calls.
   - **Fix Strategy**: Add validation: `if page < 1: page = 1` and `if page > max_pages: page = max_pages`.

5. **Weak Exception Handling in `sync_movie`**
   - **Location**: `backend/movies/services/tmdb_service.py:165-200`
   - **Issue**: Returns `None` silently without distinguishing between TMDB API failure and invalid data.
   - **Impact**: Caller doesn't know root cause; harder to retry or handle gracefully.
   - **Fix Strategy**: Raise custom exceptions (`TMDBAPIError`, `MovieNotFoundError`) with context.

6. **Service Class Not Following Dependency Injection**
   - **Location**: `backend/movies/views.py:19-20`, `backend/recommendations/views.py:20`
   - **Issue**: Global singleton instances (`tmdb = TMDBService()`, `engine = RecommendationEngine()`) created at module level.
   - **Impact**: Difficult to mock in tests; potential state sharing across requests.
   - **Fix Strategy**: Create instances per-request or inject via view initialization.

#### **MEDIUM SEVERITY** (affects maintainability/scalability)

7. **Hard-Coded Mood Genre IDs**
   - **Location**: `backend/movies/views.py:240-330` (`MOOD_MAP`)
   - **Issue**: ~90 lines of hard-coded genre IDs (e.g., `"genres": "28,53,80"`) with manual comment mapping.
   - **Impact**: Changes require code updates; no central management; error-prone.
   - **Fix Strategy**: Move `MOOD_MAP` to a dedicated config module or database model (`Mood` table).

8. **Duplicate URL Building Logic**
   - **Location**: `backend/movies/models.py:104-125` (properties) and `backend/movies/serializers.py:141-149` (serializer methods)
   - **Issue**: TMDB image URL construction repeated in 2+ places.
   - **Impact**: Brittle when base URL changes; maintainability risk.
   - **Fix Strategy**: Create single utility function `build_tmdb_image_url(path, size)` in a shared module.

9. **Duplicate Query Parameter Extraction**
   - **Location**: Multiple endpoints (`search_movies`, `trending_movies`, `mood_movies`, etc.)
   - **Issue**: Repeated code: `page = safe_int(request.query_params.get("page", 1))` and similar patterns.
   - **Impact**: If validation logic changes, must update 10+ places; inconsistency risk.
   - **Fix Strategy**: Create request parameter parser utility (`RequestParams` class or decorator).

10. **Large Static Dictionary at Module Level**
    - **Location**: `backend/movies/views.py:240-330` (`MOOD_MAP`)
    - **Issue**: 90+ lines defining 10+ moods with nested dicts.
    - **Impact**: Not DRY; hard to extend; should be configuration or database-backed.
    - **Fix Strategy**: Move to `config/moods.py` or as a database model.

11. **Missing N+1 Query in PersonDetailSerializer**
    - **Location**: `backend/movies/serializers.py:34-41` (`get_acted_movies`, `get_directed_movies`)
    - **Issue**: Calls `MovieCompactSerializer(movies, many=True)`, which in turn calls `.count()` on genres for each movie.
    - **Impact**: If a person has 20 movies with 5 genres each → 100+ extra DB queries.
    - **Fix Strategy**: Use `select_related` / `prefetch_related` in serializer or call `.only()` to limit fields.

12. **Hard-Coded Pagination Limits (10 vs 20)**
    - **Location**: Multiple files—`serializers.py:34-41` ([:20]), `engine.py:140` ([:10]), `views.py:195` ([:10])
    - **Issue**: Inconsistent limits without configuration or constants.
    - **Impact**: Can't adjust pagination globally; hard to debug why different endpoints return different result counts.
    - **Fix Strategy**: Define `PAGINATION_LIMITS` constant dict in settings; use consistently.

13. **Inconsistent Error Response Shapes**
    - **Location**: Throughout views
    - **Issue**: Some endpoints return `{"error": "..."}`, others `{"results": [...], ...}`, some include `query`, others don't.
    - **Impact**: Frontend must handle multiple response schemas; fragile integration.
    - **Fix Strategy**: Define standardized response envelope (e.g., `APIResponse` serializer).

14. **Repeated URL Building in Serializers**
    - **Location**: `backend/movies/serializers.py:141-149` (`TMDBMovieSerializer.to_representation`)
    - **Issue**: Hard-codes base URL string instead of using settings.
    - **Impact**: If URL changes, must update multiple files.
    - **Fix Strategy**: Use centralized utility function (see #8).

15. **Missing Type Hints**
    - **Location**: `backend/movies/views.py`, `backend/recommendations/services/engine.py`
    - **Issue**: Functions lack return type annotations (e.g., `def mood_movies(request, mood_slug):` should be `-> Response`).
    - **Impact**: IDE autocomplete limited; harder to catch type errors.
    - **Fix Strategy**: Add return types to all view functions and service methods.

#### **LOW SEVERITY** (technical debt / code quality)

16. **Cache Key Collision Risk**
    - **Location**: `backend/movies/views.py:39` (`build_advanced_filter_cache_key`)
    - **Issue**: Uses `f"tmdb:{endpoint}:{params}"` where `params` is a dict—dict string representation not deterministic.
    - **Impact**: Parameter order variations could fail cache lookup.
    - **Fix Strategy**: Use `json.dumps(params, sort_keys=True)` for deterministic serialization.

17. **Unused/Redundant Movie Serializer Properties**
    - **Location**: `backend/movies/serializers.py:117-149`
    - **Issue**: `TMDBMovieSerializer` includes `backdrop_url`, `poster_url_small`, `trailer_embed_url`, `year`—unclear if frontend uses all.
    - **Impact**: Dead code accumulation; technical debt.
    - **Fix Strategy**: Audit frontend usage; remove unused fields or document why they're kept.

18. **TMDB API Error Propagation Inconsistent**
    - **Location**: Various endpoints
    - **Issue**: Some use `_ensure_tmdb_ok(data)`, others check `.get("results", [])` without verifying `_error` key.
    - **Impact**: Some failures silently return empty results; inconsistent UX.
    - **Fix Strategy**: Use consistent error checking pattern across all endpoints.

19. **Boundary Conditions Not Tested**
    - **Location**: `backend/recommendations/services/engine.py:95-120` (`get_recommendations`)
    - **Issue**: If user has < 3 genres, uses all; if 0, falls back silently to trending. No explicit error handling.
    - **Impact**: Edge cases could be buggy; untested scenarios.
    - **Fix Strategy**: Add explicit checks and test coverage for zero/one/few preference cases.

20. **WatchProvider Model Unused Country Field**
    - **Location**: `backend/movies/models.py` (`WatchProvider.country_code`)
    - **Issue**: Field always "US"; never used for filtering or multi-country support.
    - **Impact**: Misleading DB schema; dead code.
    - **Fix Strategy**: Remove or implement country-based filtering globally.

21. **JSONField Default Mutable Object**
    - **Location**: `backend/users/models.py:7`, `backend/recommendations/models.py:20`
    - **Issue**: `default=list` (though DRF handles this correctly in modern Django).
    - **Impact**: Technically correct but confusing; could cause issues if model used outside DRF context.
    - **Fix Strategy**: Use `default=list` callable or explicit `default=[]` with clarifying comment.

22. **Router Registration Name Confusing**
    - **Location**: `backend/movies/urls.py:6` (`router.register(r"list", ...)`)
    - **Issue**: Endpoint is `/api/movies/list/` not `/api/movies/`; naming suggests it's a subpath.
    - **Impact**: Confusing API structure for consumers; inconsistent with REST conventions.
    - **Fix Strategy**: Register as `r""` (empty) to use `/api/movies/` + `/api/movies/{id}/`.

23. **Regex Password Validation Overly Lenient**
    - **Location**: `backend/users/serializers.py:26`
    - **Issue**: `re.search(r"[^A-Za-z0-9]", password)` allows any non-alphanumeric (space, newline, etc.).
    - **Impact**: Could accept weak passwords like `A ` or `A\n`.
    - **Fix Strategy**: Define allowed special characters set: `if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\",.<>?]", password)`

24. **Missing Request Logging/Tracing**
    - **Location**: All view functions
    - **Issue**: Failed TMDB calls only logged at service level; no request-level tracing.
    - **Impact**: Debugging production issues difficult; no correlation IDs.
    - **Fix Strategy**: Add request ID middleware; log all external API calls with context.

25. **Genre Preference Computation Inefficient**
    - **Location**: `backend/recommendations/services/engine.py:50-55`
    - **Issue**: Nested loop iterates through all interactions and genre_ids multiple times.
    - **Impact**: O(n*m) complexity; slow for users with many interactions.
    - **Fix Strategy**: Use set operations and aggregation to reduce iterations.

26. **Hardcoded Movie Comparison Limit**
    - **Location**: `backend/movies/views.py:410` (`[:2]`)
    - **Issue**: Only compares first 2 movies; hard-coded without explanation.
    - **Impact**: Can't extend to compare 3+ movies without code change.
    - **Fix Strategy**: Make configurable via query param or constant.

27. **Unused Import: `hashlib`**
    - **Location**: `backend/movies/views.py:3`
    - **Issue**: Imported but not used (MD5 hashing deferred to cache key builder).
    - **Impact**: Code clutter; if `build_advanced_filter_cache_key` is modified, this becomes needed.
    - **Fix Strategy**: Remove or document why it's imported.

28. **Validation Regex Patterns Duplicated**
    - **Location**: `backend/users/serializers.py:26-28`
    - **Issue**: Email regex pattern hard-coded; special character regex hard-coded.
    - **Impact**: If validation rules change, must update in multiple places.
    - **Fix Strategy**: Define as module-level constants (`EMAIL_PATTERN`, `SPECIAL_CHAR_PATTERN`).

---

#### **Summary of Debt by Category**

| Severity | Count | Key Areas |
|----------|-------|-----------|
| High     | 6     | Performance (500-page scan), REST violations, exception handling, DI patterns |
| Medium   | 9     | Code duplication, maintainability, schema consistency, N+1 queries |
| Low      | 13    | Technical debt, unused code, configuration, logging |
| **Total** | **28** | **Across views, services, models, serializers** |

#### **Recommended Priority for Fixes**

1. **Immediate** (blocks scaling/correctness): #2 (500-page scan), #3 (GET mutation), #5 (exception handling), #6 (global singletons)
2. **Short-term** (improves stability): #1 (giant function), #9 (duplicate params), #12 (pagination limits), #18 (error consistency)
3. **Medium-term** (tech debt): #7 (mood config), #8 (URL building), #11 (N+1), #15 (type hints), #25 (perf)
4. **Long-term** (nice-to-have): #16, #17, #20, #21, #22, #27, #28 (cleanup/polish)

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
  - `discover_filtered` moved to `MovieDiscoveryService`, with adaptive early-stop scan to replace full linear scan behavior.

