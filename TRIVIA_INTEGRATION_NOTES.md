# Daily Trivia Integration Notes

All trivia feature code was added in new files only.

## New backend files

- `backend/trivia/apps.py`
- `backend/trivia/urls.py`
- `backend/trivia/views.py`
- `backend/trivia/services/daily_trivia_service.py`

## New frontend files

- `frontend/src/types/trivia.ts`
- `frontend/src/lib/trivia-api.ts`
- `frontend/src/components/trivia/DailyTriviaGame.tsx`
- `frontend/src/app/trivia/page.tsx`

## Minimal wiring required (manual)

These two tiny integrations are required to make the feature reachable:

1. Register the backend trivia routes:
   - Include `trivia.urls` in `backend/cinequest/urls.py` under the `/api/` prefix.
2. Add a nav link in `frontend/src/components/Navbar.tsx`:
   - Add `{ href: "/trivia", label: "Daily Trivia", ... }` to existing links.

Without those two wiring lines, the new code is present but not reachable from existing routes/navigation.

