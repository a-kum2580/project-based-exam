# Software Construction Exam Project

A full-stack movie discovery platform built with **Django REST Framework** (backend) and **Next.js** (frontend), powered by The Movie Database (TMDB) API.

## Project Structure

```
├── backend/          # Django REST API
│   ├── cinequest/    # Project settings & URLs
│   ├── movies/       # Movies app (models, views, TMDB service)
│   ├── users/        # Custom user model & auth
│   └── recommendations/  # Recommendation engine & watchlist
├── frontend/         # Next.js application
│   ├── src/app/      # Pages (home, search, movie detail, etc.)
│   ├── src/components/  # Reusable UI components
│   ├── src/lib/      # API client, auth context, utilities
│   └── src/types/    # TypeScript type definitions
```

## Getting Started

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py sync_movies --genres
python manage.py sync_movies --trending 2
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Create a `.env` file in the `backend/` directory using `.env.example` as a template:

```bash
cp .env.example .env
Then fill in your actual values:

- `TMDB_API_KEY` - Get your free API key from https://www.themoviedb.org/settings/api
- `DJANGO_SECRET_KEY` - Any random secret string
- `DEBUG` - Set to `True` for development, `False` for production
- `ALLOWED_HOSTS` - Comma separated list of allowed hosts
- `CORS_ORIGINS` - Comma separated list of allowed frontend origins

> **Note:** Never commit your `.env` file to GitHub. It is already listed in `.gitignore`.

### Auth & Registration Rules (Backend)
- **Username uniqueness is case-insensitive**: `Shira` and `shira` are treated as the same username.
- **Login is case-insensitive**: you can sign in with any casing of your username.
- **Password rules (in addition to Django validators)**:
  - Must start with a **capital letter**
  - Must include at least **one special character** (e.g. `!@#$`)

### Backend API Tests Explained

The backend test suite includes both API tests and service-level tests. The two API tests we ran one at a time are:

- **JWT login API test** - [backend/users/tests.py](backend/users/tests.py)
  - Test name: `JWTAuthTest.test_obtain_token_is_case_insensitive`
  - Endpoint: `POST /api/auth/token/`
  - What it checks:
    - the login endpoint accepts a username in a different case from the one stored in the database
    - the custom JWT serializer maps the submitted username to the stored username using a case-insensitive lookup
    - a valid password still returns `access` and `refresh` tokens
  - Why it matters:
    - the project treats usernames as case-insensitive for login, so users do not need to remember exact capitalization
    - this test proves the custom token view and serializer are wired correctly

- **Because-you-watched recommendations API test** - [backend/recommendations/tests.py](backend/recommendations/tests.py)
  - Test name: `BecauseYouWatchedAPITest.test_because_you_watched_serializes_nested_movie_groups`
  - Endpoint: `GET /api/recommendations/because-you-watched/`
  - What it checks:
    - the endpoint returns grouped recommendation results keyed by source movie title
    - nested movie lists are serialized into API-safe JSON using `TMDBMovieSerializer`
    - the response preserves the expected shape for the frontend
  - Why it matters:
    - the frontend depends on this grouped structure to render recommendations per watched movie
    - this test verifies that response formatting is correct, not just that the engine returns data

### Other Backend Coverage

The backend test suite also includes service-level checks that validate movie sync behavior:

- `MovieSyncServiceTest.test_sync_movie_creates_all_related_models`
  - verifies that syncing a TMDB movie creates the movie, genres, directors, cast, trailer key, and watch providers
- `MovieSyncServiceTest.test_sync_movie_raises_api_error_on_tmdb_failure`
  - verifies that TMDB errors are surfaced as `TMDBAPIError`
- `MovieSyncServiceTest.test_sync_movie_raises_not_found_for_invalid_payload`
  - verifies that invalid TMDB payloads raise `MovieNotFoundError`

These tests are useful for proving that the backend handles both success and failure paths consistently.

## TMDB API
Get your free API key at: https://www.themoviedb.org/settings/api
# project-based-exam