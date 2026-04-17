# Contributions Report

This report summarizes repository contributions based on git history.

Scope and method:
- Source: git log on this repository
- Metrics: non-merge commits, changed files, insertions, deletions, and area touched
- Snapshot date: 2026-04-16
- Note: some teammates may appear under multiple identities (for example personal email and GitHub noreply email).

## 1) Team Contribution Graphs

### Commit Share by Member (non-merge commits)

```mermaid
pie title Commit Share by Member (Total = 101)
  "Shiramiki" : 37
  "a-kum2580" : 28
  "Charis-Opol" : 8
  "Emma k" : 8
  "Ariko Ethan" : 5
  "Isooba Mbeiza Rachel" : 3
  "Anthony Ssetimba" : 3
  "Others" : 9
```

### Top Contributors by Files Touched

```mermaid
xychart-beta
  title "Top Contributors - Files Touched"
  x-axis ["Shiramiki", "muganga-charles", "a-kum2580", "Charis-Opol", "Emma k"]
  y-axis "Files" 0 --> 140
  bar [131, 77, 32, 16, 8]
```

## 2) Summary Table (non-merge commits)

| Member | Commits | Files Touched | Insertions | Deletions |
|---|---:|---:|---:|---:|
| Shiramiki | 37 | 131 | 4164 | 1218 |
| a-kum2580 | 28 | 32 | 1102 | 680 |
| Charis-Opol | 8 | 16 | 584 | 395 |
| Emma k | 8 | 8 | 32 | 46 |
| Ariko Ethan | 5 | 5 | 249 | 348 |
| Isooba Mbeiza Rachel | 3 | 6 | 349 | 250 |
| Anthony Ssetimba | 3 | 3 | 414 | 0 |
| Tola144 | 2 | 4 | 53 | 2 |
| Haider0012831 | 2 | 2 | 43 | 2 |
| lomoro paul | 2 | 2 | 38 | 21 |
| muganga-charles | 2 | 77 | 12996 | 0 |
| CarolNaddunga | 1 | 5 | 51 | 41 |

## 3) Detailed Contributions by Member (Files + Responsibilities)

### Shiramiki
- Main areas: backend (89), frontend (32), docs (10).
- Core responsibilities: recommendation engine evolution, dashboard analytics, search and mood UX flows, API robustness.
- High-impact files changed:
  - backend/recommendations/views.py (14 touches)
  - backend/recommendations/tests.py (12)
  - backend/movies/views.py (10)
  - frontend/src/app/dashboard/page.tsx (8)
  - backend/recommendations/services/engine.py (5)
  - frontend/src/app/movie/[id]/page.tsx (5)
  - frontend/src/app/search/page.tsx (5)
  - backend/movies/services/discovery_service.py (5)
  - backend/movies/services/tmdb_service.py (5)

### a-kum2580
- Main areas: backend (25), frontend (4), docs (3).
- Core responsibilities: backend reliability, user validation paths, serializer/API hardening, technical report updates.
- High-impact files changed:
  - backend/users/serializers.py (4 touches)
  - backend/users/tests.py (4)
  - backend/movies/tests.py (2)
  - backend/movies/test_views.py (2)
  - backend/movies/test_serializers.py (2)
  - backend/cinequest/settings.py (2)
  - BACKEND_TECHNICAL_REPORT.md (2)

### muganga-charles
- Main areas: backend (41), frontend (34), docs (1), other (1).
- Core responsibilities: baseline codebase initialization and broad project scaffolding.
- Representative files changed:
  - backend/cinequest/settings.py
  - backend/movies/models.py
  - backend/movies/views.py
  - backend/recommendations/views.py
  - backend/users/models.py
  - frontend/src/app/page.tsx
  - frontend/src/app/dashboard/page.tsx
  - frontend/src/app/search/page.tsx
  - frontend/src/components/Navbar.tsx

### Charis-Opol
- Main areas: frontend (16).
- Core responsibilities: frontend refactoring and DRY improvements.
- High-impact files changed:
  - frontend/src/app/page.tsx (4 touches)
  - frontend/src/app/compare/page.tsx (4)
  - frontend/src/components/PersonalizedSection.tsx (3)
  - frontend/src/components/HeroSection.tsx (3)

### Emma k
- Main areas: backend (8).
- Core responsibilities: TMDB service and serializer/view optimizations.
- High-impact files changed:
  - backend/movies/views.py (3 touches)
  - backend/movies/services/tmdb_service.py (3)
  - backend/movies/serializers.py (2)

### Ariko Ethan
- Main areas: frontend (5).
- Core responsibilities: movie/search UI data-shaping and safer API result handling.
- High-impact files changed:
  - frontend/src/lib/api.ts (2 touches)
  - frontend/src/types/movie.ts
  - frontend/src/app/movie/[id]/page.tsx
  - frontend/src/app/search/page.tsx

### Isooba Mbeiza Rachel
- Main areas: frontend (4), docs (2).
- Core responsibilities: search-page and movie-page maintenance plus documentation cleanup.
- High-impact files changed:
  - README.md (2 touches)
  - frontend/src/app/search/page.tsx
  - frontend/src/app/movie/[id]/page.tsx
  - frontend/src/lib/api.ts
  - frontend/src/types/movie.ts

### Anthony Ssetimba
- Main areas: backend testing (3).
- Core responsibilities: expanding app-level test coverage.
- Files changed:
  - backend/recommendations/tests.py
  - backend/movies/tests.py
  - backend/users/tests.py

### CarolNaddunga
- Main areas: backend (4), docs (1).
- Core responsibilities: recommendations service and settings wiring.
- Files changed:
  - backend/recommendations/views.py
  - backend/recommendations/services/engine.py
  - backend/cinequest/settings.py
  - backend/.env.example
  - README.md

### Tola144
- Main areas: backend setup (3), repo governance (1).
- Files changed:
  - backend/cinequest/asgi.py
  - backend/cinequest/settings.py
  - backend/cinequest/urls.py
  - .github/CODEOWNERS

### Haider0012831
- Main areas: frontend testing/build config (2).
- Files changed:
  - frontend/src/app/search/Navbar.test.tsx
  - frontend/src/app/globals.css

### lomoro paul
- Main areas: frontend search/mood flow (2).
- Files changed:
  - frontend/src/app/search/page.tsx
  - frontend/src/app/mood/page.tsx

## 4) Who Tested What

This section is based on test-file modifications and test-focused commit subjects.

### Testing Contribution Graph (test files touched)

```mermaid
xychart-beta
  title "Testing Contributions by Member"
  x-axis ["Shiramiki", "a-kum2580", "Anthony", "Haider"]
  y-axis "Test files touched" 0 --> 5
  bar [4, 4, 3, 1]
```

| Member | Evidence of Testing Contribution | Test Files |
|---|---|---|
| Shiramiki | Expanded recommendation and movie regression coverage; added focused validation script | backend/recommendations/tests.py, backend/movies/tests.py, backend/users/tests.py, backend/test_weights.py |
| a-kum2580 | Added and updated multiple backend test suites and dedicated movie test modules | backend/users/tests.py, backend/movies/tests.py, backend/movies/test_views.py, backend/movies/test_serializers.py, backend/recommendations/tests.py |
| Anthony Ssetimba | Added app-specific tests for users, movies, and recommendations | backend/users/tests.py, backend/movies/tests.py, backend/recommendations/tests.py |
| Haider0012831 | Added frontend component test | frontend/src/app/search/Navbar.test.tsx |

No direct test-file edits were found for some members; their contributions were primarily implementation/refactor/configuration work.

## 5) Area Distribution by Member (files touched)

| Member | Backend | Frontend | Docs | Other |
|---|---:|---:|---:|---:|
| Shiramiki | 89 | 32 | 10 | 0 |
| muganga-charles | 41 | 34 | 1 | 1 |
| a-kum2580 | 25 | 4 | 3 | 0 |
| Charis-Opol | 0 | 16 | 0 | 0 |
| Emma k | 8 | 0 | 0 | 0 |
| Isooba Mbeiza Rachel | 0 | 4 | 2 | 0 |
| CarolNaddunga | 4 | 0 | 1 | 0 |
| Ariko Ethan | 0 | 5 | 0 | 0 |
| Tola144 | 3 | 0 | 0 | 1 |
| Anthony Ssetimba | 3 | 0 | 0 | 0 |
| lomoro paul | 0 | 2 | 0 | 0 |
| Haider0012831 | 0 | 2 | 0 | 0 |

## 6) Current Branch Note (Isooba_M_Rachel vs main)

For commits ahead of main in the current branch, the recorded author is:
- Shiramiki

This means the active branch work currently reflects a single contributor identity on top of main.
