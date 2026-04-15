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
  - `python manage.py test movies recommendations users` after smells #3-#6 fixes → PASS (51 tests)
  - `python manage.py test movies recommendations users` after smells #7-#17 work → PASS (51 tests)
  - `python manage.py test movies recommendations users` after smells #18-#28 work → PASS (54 tests)
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
   - **Solution Implemented**: Keep GET endpoint but make enrichment response-only (no persistence).

   **What changed in code**
   - `PersonViewSet.enrich` now:
     - fetches TMDB details
     - serializes the existing local person
     - overlays response fields (`biography`, `birthday`, `place_of_birth`) in-memory
     - returns enriched payload without calling `.save()`
   - This preserves endpoint compatibility while removing side effects.

   **Why this fix was selected**
   - avoids a breaking API contract change from GET to POST
   - restores GET idempotency
   - still provides fresh enrichment data to clients

4. **Missing Pagination Boundary Checks**
   - **Location**: Throughout views (especially `discover_filtered`)
   - **Issue**: `page` parameter not validated for negative values or absurd ranges (e.g., `?page=-999` or `?page=99999`).
   - **Impact**: Invalid queries could bypass caching or cause unexpected API calls.
   - **Solution Implemented**: Added bounded page parsing in both movies and recommendations flows.

   **What changed in code**
   - Added `safe_page(...)` in `backend/movies/views.py`:
     - coerces invalid/negative pages to `1`
     - caps large pages at `MAX_PAGE=500`
   - Applied `safe_page(...)` to movie endpoints using `page`:
     - genres list fallback
     - search, trending, now-playing, top-rated, moods
   - In discovery service, `parse_request_filters(...)` now uses `_sanitize_page(...)` for bounded pages.
   - In recommendations, `_parse_page(...)` now caps to `MAX_PAGE=500`.

   **Result**
   - no negative page numbers reach TMDB calls
   - very large page inputs are bounded consistently
   - paging behavior is deterministic across endpoints

5. **Weak Exception Handling in `sync_movie`**
   - **Location**: `backend/movies/services/tmdb_service.py:165-200`
   - **Issue**: Returns `None` silently without distinguishing between TMDB API failure and invalid data.
   - **Impact**: Caller doesn't know root cause; harder to retry or handle gracefully.
   - **Solution Implemented**: Introduced explicit domain exceptions with contextual messages.

   **What changed in code**
   - Added custom exceptions in `backend/movies/services/tmdb_service.py`:
     - `TMDBAPIError`
     - `MovieNotFoundError`
   - `MovieSyncService.sync_movie(...)` now:
     - raises `TMDBAPIError` when TMDB returns `_error`
     - raises `MovieNotFoundError` when payload lacks a valid movie `id`
   - `sync_trending(...)` now catches these exceptions per movie, logs context, and continues.
   - `movie_detail_tmdb` endpoint now maps exceptions explicitly:
     - `MovieNotFoundError` -> 404 response
     - `TMDBAPIError` -> APIException (502-style DRF error path)
   - `sync_movies` management command now catches and prints these exceptions clearly.

   **Result**
   - failure modes are now explicit and actionable
   - callers can distinguish remote API failure from invalid/missing movie payload
   - trending sync is more resilient (one bad item no longer aborts batch)

6. **Service Class Not Following Dependency Injection**
   - **Location**: `backend/movies/views.py:19-20`, `backend/recommendations/views.py:20`
   - **Issue**: Global singleton instances (`tmdb = TMDBService()`, `engine = RecommendationEngine()`) created at module level.
   - **Impact**: Difficult to mock in tests; potential state sharing across requests.
   - **Solution Implemented**: Replaced module-level singletons with provider functions (per-request construction).

   **What changed in code**
   - In `backend/movies/views.py`, added providers:
     - `get_tmdb_service()`
     - `get_movie_sync_service(tmdb_service=...)`
     - `get_discovery_service(tmdb_service)`
   - Endpoints/actions now resolve services via providers instead of global instances.
   - In `backend/recommendations/views.py`, replaced global `engine` with `get_recommendation_engine()` and resolved engine inside each endpoint.
   - Tests updated to patch provider functions (`movies.views.get_tmdb_service`) instead of patching global service objects.

   **Why this improves design**
   - test mocking is simpler and more reliable
   - avoids accidental shared mutable state at module level
   - supports future dependency overrides (factory-based injection)

#### **MEDIUM SEVERITY** (affects maintainability/scalability)

7. **Hard-Coded Mood Genre IDs**
   - **Location**: `backend/movies/views.py:240-330` (`MOOD_MAP`)
   - **Issue**: ~90 lines of hard-coded genre IDs (e.g., `"genres": "28,53,80"`) with manual comment mapping.
   - **Impact**: Changes require code updates; no central management; error-prone.
  - **Solution Implemented**: Moved mood definitions into dedicated config module.

  **What changed in code**
  - Added `backend/movies/config/moods.py` with `MOOD_MAP`.
  - Removed large inline mood dict from `backend/movies/views.py`.
  - `mood_list` and `mood_movies` now consume shared config import.

  **Result**
  - mood definitions are centrally managed
  - view complexity reduced
  - future updates no longer require editing endpoint code

8. **Duplicate URL Building Logic**
   - **Location**: `backend/movies/models.py:104-125` (properties) and `backend/movies/serializers.py:141-149` (serializer methods)
   - **Issue**: TMDB image URL construction repeated in 2+ places.
   - **Impact**: Brittle when base URL changes; maintainability risk.
   - **Solution Implemented**: Introduced shared media URL helper functions and wired models/serializers to them.

   **What changed in code**
   - Added `backend/movies/utils/media.py`:
     - `build_tmdb_image_url(path, size)`
     - `build_youtube_watch_url(video_key)`
     - `build_youtube_embed_url(video_key)`
   - Updated `backend/movies/models.py` properties (`profile_url`, `poster_url`, `poster_url_small`, `backdrop_url`, `trailer_url`, `trailer_embed_url`, `logo_url`) to use shared helpers.

   **Result**
   - one source of truth for media URL construction
   - lower risk when URL patterns or base path changes

9. **Duplicate Query Parameter Extraction**
   - **Location**: Multiple endpoints (`search_movies`, `trending_movies`, `mood_movies`, etc.)
   - **Issue**: Repeated code: `page = safe_int(request.query_params.get("page", 1))` and similar patterns.
   - **Impact**: If validation logic changes, must update 10+ places; inconsistency risk.
   - **Solution Implemented**: Added utility parser and replaced duplicated extraction in movie endpoints.

   **What changed in code**
   - Added `backend/movies/utils/query_params.py` with `RequestParams` helper:
     - `page(...)`, `text(...)`, `int_or_none(...)`, `float_or_none(...)`
   - Updated `backend/movies/views.py` endpoints to use parser (`search_movies`, `trending_movies`, `now_playing`, `top_rated`, `mood_movies`, genres action).

   **Result**
   - reduced repetitive parsing code
   - consistent conversion and defaults across endpoints

10. **Large Static Dictionary at Module Level**
    - **Location**: `backend/movies/views.py:240-330` (`MOOD_MAP`)
    - **Issue**: 90+ lines defining 10+ moods with nested dicts.
    - **Impact**: Not DRY; hard to extend; should be configuration or database-backed.
    - **Solution Implemented**: Moved mood dictionary to `backend/movies/config/moods.py` (shared module-level config).

    **Result**
    - removed large constant block from view module
    - improved readability and maintainability of `movies/views.py`

11. **Missing N+1 Query in PersonDetailSerializer**
    - **Location**: `backend/movies/serializers.py:34-41` (`get_acted_movies`, `get_directed_movies`)
    - **Issue**: Calls `MovieCompactSerializer(movies, many=True)`, which in turn calls `.count()` on genres for each movie.
    - **Impact**: If a person has 20 movies with 5 genres each → 100+ extra DB queries.
    - **Solution Implemented**: Reduced nested query pressure by prefetching and removing expensive nested genre count field in embedded movie payloads.

    **What changed in code**
    - Added `GenreCompactSerializer` (no `movie_count`) for embedded movie genres.
    - Updated `MovieCompactSerializer` and `MovieDetailSerializer` to use `GenreCompactSerializer`.
    - Updated `PersonDetailSerializer` queries to use `.prefetch_related("genres")` for directed/acted movie lists.

    **Result**
    - avoids repeated `obj.movies.count()` calls per embedded genre in person detail responses
    - fewer queries for person detail endpoints with large filmographies

12. **Hard-Coded Pagination Limits (10 vs 20)**
    - **Location**: Multiple files—`serializers.py:34-41` ([:20]), `engine.py:140` ([:10]), `views.py:195` ([:10])
    - **Issue**: Inconsistent limits without configuration or constants.
    - **Impact**: Can't adjust pagination globally; hard to debug why different endpoints return different result counts.
    - **Solution Implemented**: Added centralized limit constants in settings and applied them across serializers/services/views.

    **What changed in code**
    - Added `PAGINATION_LIMITS` dict in `backend/cinequest/settings.py`.
    - Applied settings limits in:
      - `backend/movies/serializers.py` (`person_movies`, `movie_cast`)
      - `backend/recommendations/services/engine.py` (`top_genres`, `director_recommendations`, `because_you_watched_*`)
      - `backend/recommendations/views.py` (`recent_interactions`, `max_page`)
      - `backend/movies/views.py` (`compare_movies`, `max_page`)

    **Result**
    - limit values are now centralized and consistent
    - behavior changes can be made from settings without touching business logic

13. **Inconsistent Error Response Shapes**
    - **Location**: Throughout views
    - **Issue**: Some endpoints return `{"error": "..."}`, others `{"results": [...], ...}`, some include `query`, others don't.
    - **Impact**: Frontend must handle multiple response schemas; fragile integration.
    - **Solution Implemented (Phase 1)**: Added unified error response helper in movies endpoints while preserving existing successful payload contracts.

    **What changed in code**
    - Added `error_response(message, status_code)` helper in `backend/movies/views.py`.
    - Replaced multiple ad-hoc error `Response(...)` constructions with helper in updated endpoints.

    **Result**
    - reduced error-shape drift in movies API
    - backward compatibility maintained for successful responses

    **Remaining scope**
    - full cross-app response envelope standardization (movies/users/recommendations) remains a broader follow-up.

14. **Repeated URL Building in Serializers**
    - **Location**: `backend/movies/serializers.py:141-149` (`TMDBMovieSerializer.to_representation`)
    - **Issue**: Hard-codes base URL string instead of using settings.
    - **Impact**: If URL changes, must update multiple files.
    - **Solution Implemented**: `TMDBMovieSerializer.to_representation` now uses shared media helper.

    **What changed in code**
    - Replaced hard-coded base URL assembly with `build_tmdb_image_url(...)` in `backend/movies/serializers.py`.

    **Result**
    - serializer URL generation now matches model URL generation source-of-truth.

15. **Missing Type Hints**
    - **Location**: `backend/movies/views.py`, `backend/recommendations/services/engine.py`
    - **Issue**: Functions lack return type annotations (e.g., `def mood_movies(request, mood_slug):` should be `-> Response`).
    - **Impact**: IDE autocomplete limited; harder to catch type errors.
    - **Solution Implemented (targeted)**: Added type hints to high-traffic and refactored methods/functions.

    **What changed in code**
    - Added return type hints in key movie endpoints (`search_movies`, `trending_movies`, `now_playing`, `top_rated`, `movie_detail_tmdb`, `search_people`, `mood_list`, `mood_movies`, `discover_filtered`, `compare_movies`).
    - Added typed signatures in `backend/recommendations/services/engine.py` for core methods.
    - Added typed utility signatures in request parsing and discovery helper methods.

    **Result**
    - better static tooling support and IDE guidance in critical paths.

#### **LOW SEVERITY** (technical debt / code quality)

16. **Cache Key Collision Risk**
    - **Location**: `backend/movies/services/tmdb_service.py` (`TMDBService._get` cache key)
    - **Issue**: Uses `f"tmdb:{endpoint}:{params}"` where `params` is a dict—dict string representation not deterministic.
    - **Impact**: Parameter order variations could fail cache lookup.
    - **Solution Implemented**: Cache key serialization normalized with sorted JSON.

    **What changed in code**
    - In `TMDBService._get`, cache key now uses:
      - `normalized_params = json.dumps(params or {}, sort_keys=True)`
      - `cache_key = f"tmdb:{endpoint}:{normalized_params}"`

    **Result**
    - deterministic cache keys
    - better cache hit consistency and no dict-order drift

17. **Unused/Redundant Movie Serializer Properties**
    - **Location**: `backend/movies/serializers.py:117-149`
    - **Issue**: `TMDBMovieSerializer` includes `backdrop_url`, `poster_url_small`, `trailer_embed_url`, `year`—unclear if frontend uses all.
    - **Impact**: Dead code accumulation; technical debt.
    - **Solution Implemented**: Audited frontend usage and retained contract-relevant fields; no removal done to avoid regressions.

    **Audit outcome**
    - `year`, `poster_url_small`, and `backdrop_url` are used by frontend components and types.
    - `trailer_embed_url` remains part of detail payload contract and is kept for compatibility.

    **Result**
    - avoided unsafe field removals
    - contract preserved while refactoring surrounding duplication (#8/#14)

18. **TMDB API Error Propagation Inconsistent**
    - **Location**: Various endpoints
    - **Issue**: Some use `_ensure_tmdb_ok(data)`, others check `.get("results", [])` without verifying `_error` key.
    - **Impact**: Some failures silently return empty results; inconsistent UX.
    - **Solution Implemented**: Applied consistent TMDB error checks in movies endpoints and recommendations engine.

    **What changed in code**
    - Updated `backend/movies/views.py` to call `_ensure_tmdb_ok(...)` on TMDB-backed actions/endpoints that previously skipped validation:
      - movie recommendations/similar
      - genre fallback list
      - mood movies
      - compare movies
    - Added request-aware context logging inside `_ensure_tmdb_ok(...)` so failures include:
      - `request_id`
      - endpoint context label
      - TMDB error payload
    - Added `RecommendationEngine._ensure_tmdb_ok(...)` and used it for:
      - trending fallback
      - per-genre discover calls
      - because-you-watched calls

    **Result**
    - TMDB failures are now surfaced consistently instead of silently returning empty lists.
    - error diagnostics are traceable by request id and endpoint context.

19. **Boundary Conditions Not Tested**
    - **Location**: `backend/recommendations/services/engine.py:95-120` (`get_recommendations`)
    - **Issue**: If user has < 3 genres, uses all; if 0, falls back silently to trending. No explicit error handling.
    - **Impact**: Edge cases could be buggy; untested scenarios.
    - **Solution Implemented**: Added explicit boundary handling plus dedicated tests.

    **What changed in code**
    - In `backend/recommendations/services/engine.py`, `get_recommendations(...)` now explicitly handles:
      - empty preferences -> trending fallback
      - empty `top_genres` after slicing -> trending fallback
    - Added tests in `backend/recommendations/tests.py`:
      - `test_empty_top_genres_falls_back_to_trending`
      - `test_single_preference_genre_works`

    **Result**
    - fallback behavior is explicit and covered by tests for edge preference distributions.

20. **WatchProvider Model Unused Country Field**
    - **Location**: `backend/movies/models.py` (`WatchProvider.country_code`)
    - **Issue**: Field always "US"; never used for filtering or multi-country support.
    - **Impact**: Misleading DB schema; dead code.
    - **Solution Implemented**: Implemented country-aware watch provider sync + response filtering.

    **What changed in code**
    - Added settings in `backend/cinequest/settings.py`:
      - `DEFAULT_PROVIDER_COUNTRY`
      - `WATCH_PROVIDER_COUNTRIES`
    - Updated `MovieSyncService.sync_movie(...)` in `backend/movies/services/tmdb_service.py`:
      - syncs provider rows for configured countries
      - stores actual `country_code` per provider row
    - Updated `MovieDetailSerializer` in `backend/movies/serializers.py`:
      - `watch_providers` now filters by `country` query param
      - falls back to authenticated user `country_code`
      - then falls back to default provider country

    **Result**
    - `country_code` field is now functionally used and no longer dead schema.

21. **JSONField Default Mutable Object**
    - **Location**: `backend/users/models.py:7`, `backend/recommendations/models.py:20`
    - **Issue**: `default=list` (though DRF handles this correctly in modern Django).
    - **Impact**: Technically correct but confusing; could cause issues if model used outside DRF context.
    - **Solution Implemented**: Retained callable defaults and documented intent explicitly.

    **What changed in code**
    - Added clarifying comments on JSONField definitions using `default=list` in:
      - `backend/users/models.py`
      - `backend/recommendations/models.py`

    **Result**
    - behavior stays correct (callable default) and maintainers get explicit guidance on why this is safe.

22. **Router Registration Name Confusing**
    - **Location**: `backend/movies/urls.py:6` (`router.register(r"list", ...)`)
    - **Issue**: Endpoint is `/api/movies/list/` not `/api/movies/`; naming suggests it's a subpath.
    - **Impact**: Confusing API structure for consumers; inconsistent with REST conventions.
    - **Solution Implemented**: Made router root canonical while preserving legacy compatibility routes.

    **What changed in code**
    - In `backend/movies/urls.py`:
      - switched canonical registration to `router.register(r"", views.MovieViewSet, basename="movie")`
      - preserved old client compatibility with aliases:
        - `/api/movies/list/`
        - `/api/movies/list/<id>/`
      - ordered router registrations so specific prefixes (`genres`, `people`) resolve before root.

    **Result**
    - RESTful canonical route is now `/api/movies/`.
    - existing clients using `/api/movies/list/` continue to work.

23. **Regex Password Validation Overly Lenient**
    - **Location**: `backend/users/serializers.py:26`
    - **Issue**: `re.search(r"[^A-Za-z0-9]", password)` allows any non-alphanumeric (space, newline, etc.).
    - **Impact**: Could accept weak passwords like `A ` or `A\n`.
    - **Solution Implemented**: Replaced broad non-alphanumeric check with explicit allowed special-character pattern.

    **What changed in code**
    - In `backend/users/serializers.py`:
      - added `SPECIAL_CHAR_PATTERN`
      - validation now uses `re.search(SPECIAL_CHAR_PATTERN, password)`
    - Added regression coverage in `backend/users/tests.py`:
      - `test_register_rejects_whitespace_only_symbol_password`

    **Result**
    - passwords with only whitespace/non-visible symbols no longer satisfy special-char rule.

24. **Missing Request Logging/Tracing**
    - **Location**: All view functions
    - **Issue**: Failed TMDB calls only logged at service level; no request-level tracing.
    - **Impact**: Debugging production issues difficult; no correlation IDs.
    - **Solution Implemented (Phase 1)**: Added request-id middleware and TMDB failure context logging.

    **What changed in code**
    - Added `backend/cinequest/middleware.py` with `RequestIdMiddleware`:
      - assigns/propagates `X-Request-ID`
      - attaches `request.request_id`
    - Registered middleware in `backend/cinequest/settings.py`.
    - Updated movies TMDB error handling logs to include `request_id` and endpoint context.

    **Result**
    - request-level tracing now exists for TMDB failures in movie endpoints.

    **Remaining scope**
    - full cross-app structured logging for all outbound calls can be expanded in a dedicated observability pass.

25. **Genre Preference Computation Inefficient**
    - **Location**: `backend/recommendations/services/engine.py:50-55`
    - **Issue**: Nested loop iterates through all interactions and genre_ids multiple times.
    - **Impact**: O(n*m) complexity; slow for users with many interactions.
    - **Solution Implemented**: Removed repeated inner scans by tracking interaction counts during single pass.

    **What changed in code**
    - In `backend/recommendations/services/engine.py`:
      - added `genre_interaction_counts = Counter()`
      - incremented interaction count in the existing loop
      - replaced per-genre `sum(...)` recomputation with O(1) counter lookup

    **Result**
    - avoids repeated scans over the full interaction queryset for each genre.
    - lower compute overhead for active users.

26. **Hardcoded Movie Comparison Limit**
    - **Location**: `backend/movies/views.py:410` (`[:2]`)
    - **Issue**: Only compares first 2 movies; hard-coded without explanation.
    - **Impact**: Can't extend to compare 3+ movies without code change.
    - **Solution Implemented**: Comparison minimum/count uses centralized settings constant.

    **What changed in code**
    - `backend/cinequest/settings.py` now defines `PAGINATION_LIMITS["compare_movies"]`.
    - `backend/movies/views.py::compare_movies` uses this constant for:
      - minimum input validation
      - slice count for fetched movie ids

    **Result**
    - compare-limit behavior is configurable without endpoint code changes.

27. **Unused Import: `hashlib`**
    - **Location**: `backend/movies/views.py:3`
    - **Issue**: Imported but not used (MD5 hashing deferred to cache key builder).
    - **Impact**: Code clutter; if `build_advanced_filter_cache_key` is modified, this becomes needed.
    - **Solution Implemented**: Removed unused import from views and kept hashing only where it is actively used.

    **What changed in code**
    - `backend/movies/views.py` no longer imports `hashlib`.
    - hash usage remains in cache-key generation utilities where required.

    **Result**
    - reduced dead imports and lint noise.

28. **Validation Regex Patterns Duplicated**
    - **Location**: `backend/users/serializers.py:26-28`
    - **Issue**: Email regex pattern hard-coded; special character regex hard-coded.
    - **Impact**: If validation rules change, must update in multiple places.
    - **Solution Implemented**: Moved regex literals to module-level constants and reused them.

    **What changed in code**
    - In `backend/users/serializers.py`:
      - added `EMAIL_PATTERN`
      - added `SPECIAL_CHAR_PATTERN`
      - email and password validators now reference shared constants

    **Result**
    - validation rules are centralized and easier to update safely.

---

#### **Summary of Debt by Category**

| Severity | Count | Key Areas |
|----------|-------|-----------|
| High     | 6     | Performance (500-page scan), REST violations, exception handling, DI patterns |
| Medium   | 9     | Code duplication, maintainability, schema consistency, N+1 queries |
| Low      | 13    | Technical debt, unused code, configuration, logging |
| **Total** | **28** | **Across views, services, models, serializers** |


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
  - `PersonViewSet.enrich` changed to side-effect-free GET enrichment response (no DB write).
  - paging now uses bounded page parsing across movies/recommendations (`1..500`).
  - sync flow now raises and handles explicit exceptions (`TMDBAPIError`, `MovieNotFoundError`).
  - module-level service singletons replaced with provider-based dependency construction in views.
  - mood configuration extracted from views into dedicated config module.
  - media URL construction centralized into shared helper utilities and reused in models/serializers.
  - reusable query parameter parser added and wired into movie endpoints.
  - centralized `PAGINATION_LIMITS` added in settings and adopted across views/serializers/services.
  - deterministic TMDB cache key serialization implemented using sorted JSON params.
  - TMDB error checks standardized across movie endpoints and recommendation engine calls.
  - request-id middleware added (`X-Request-ID`) with request-aware TMDB failure logging context.
  - watch-provider country support implemented end-to-end (sync + serializer filtering).
  - movies router made canonical at `/api/movies/` with legacy `/list/` compatibility routes.
  - password/email regex rules centralized and strengthened with dedicated tests.
  - recommendation genre preference computation optimized using single-pass counters.
  - `MovieSyncService.sync_movie` decomposed into focused methods (`_upsert_movie`, `_sync_movie_genres`, `_sync_movie_people_and_cast`, `_sync_trailer`, `_sync_watch_providers`) to enforce SRP and reduce method complexity.
  - recommendation engine now uses dependency inversion with injected TMDB client and pluggable interaction weight policy.
  - recommendation weighting rules extracted into policy objects (`InteractionWeightPolicy`, `DefaultInteractionWeightPolicy`) to support OCP-style behavior extension.

## OOD Principles Applied (April 2026)

### 1) Single Responsibility Principle (SRP)
- **Before**: `MovieSyncService.sync_movie` handled payload validation, movie upsert, genres, cast/directors, trailer selection, and provider syncing in one method.
- **After**: workflow is split into cohesive private methods with one responsibility each.
- **Files**: `backend/movies/services/tmdb_service.py`
- **Benefit**: each sync stage is independently testable and safer to evolve.

### 2) Dependency Inversion Principle (DIP)
- **Before**: `RecommendationEngine` instantiated concrete `TMDBService` internally.
- **After**: `RecommendationEngine` accepts an injected TMDB client contract and injected interaction-weight policy.
- **Files**: `backend/recommendations/services/contracts.py`, `backend/recommendations/services/engine.py`, `backend/recommendations/views.py`
- **Benefit**: domain logic now depends on abstractions and can be composed differently per runtime/test context.

- **Extended coverage**: movie endpoint orchestration now depends on an application service (`MovieCatalogService`) instead of direct TMDB calls in each view function.
- **Files**: `backend/movies/services/catalog_service.py`, `backend/movies/views.py`
- **Benefit**: controllers are thinner, external-provider choreography is centralized, and endpoint behavior remains consistent.

### 3) Open/Closed Principle (OCP)
- **Before**: interaction scoring was a hard-coded constant map inside the engine.
- **After**: scoring behavior moved behind `InteractionWeightPolicy`, with default implementation `DefaultInteractionWeightPolicy`.
- **Files**: `backend/recommendations/services/policies.py`, `backend/recommendations/services/engine.py`
- **Benefit**: new scoring strategies can be introduced without modifying recommendation engine logic.

- **Extended coverage**: user registration rule evaluation is now delegated to `RegistrationValidationPolicy` rather than embedded serializer logic.
- **Files**: `backend/users/services/validation_policy.py`, `backend/users/serializers.py`
- **Benefit**: validation policy can evolve independently from transport/serialization concerns.

### 5) Additional OOD Coverage Pass
- **Movie API orchestration extraction**
  - Created `MovieCatalogService` to centralize search/trending/top-rated/now-playing/detail/people/mood catalog operations.
  - Updated movie view endpoints to orchestrate through service provider (`get_movie_catalog_service`) while preserving response contracts.
  - **Principles improved**: SRP (views focus on HTTP concerns), DIP (views depend on service abstraction boundary), DRY (shared orchestration path).
  - Composition root consistency: recommendation and movie flows now both use explicit service provider functions for dependency construction.

- **User registration policy extraction**
  - Created `RegistrationValidationPolicy` and moved password/email rule logic out of serializer.
  - Serializer now coordinates policy + Django validator invocation rather than implementing raw regex checks directly.
  - **Principles improved**: SRP (serializer as transport mapper), OCP (new policy rules can be added in policy class).

### 4) Validation Evidence
- `python manage.py test movies recommendations users` -> **PASS (55 tests)**
- Added focused test: injected custom weight policy changes normalized preference outcome.
- **File**: `backend/recommendations/tests.py`
- Re-ran after broader movies/users OOD refactor pass: **PASS (55 tests)**.
- Re-ran after final composition-root consistency updates (recommendations view + sync command): **PASS (55 tests)**.

