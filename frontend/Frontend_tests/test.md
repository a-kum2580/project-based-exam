# Testing Documentation & Technical Report

This document outlines the testing strategy, the test suites implemented for the CineQuest frontend and backend, an analysis of our coverage gaps, and instructions on how to run the tests.

## 1. What was tested and why those areas were chosen

We prioritized testing areas that have the highest impact on user experience, application stability, and core business logic.

### Frontend Tests
1. **`HeroSection.test.tsx` (Component/Safety Test)**
   * **Why**: To prevent runtime crashes. A previous bug caused `.slice is not a function` when `undefined` was passed. This ensures the component gracefully falls back to a safe UI.
2. **`Navbar.test.tsx` (Integration/Auth Test)**
   * **Why**: Authentication state dictates main navigation. Mocking `useAuth` ensures guests see "Sign In" while authenticated users see their profile/dashboard.
3. **`HomePage.test.tsx` (Async Data Fetching Test)**
   * **Why**: Coordinates multiple API calls. Ensures the page doesn't crash during loading and correctly renders child components once promises resolve.
4. **`MovieCard.test.tsx` (Unit/Prop Logic Test)**
   * **Why**: Reused heavily throughout the app. Ensures conditional rendering (hiding overview, displaying ratings) works based on dynamic props.
5. **`SearchModal.test.tsx` (Integration/Debounce Test)**
   * **Why**: Search functionality is complex. Verifies that fast typing is debounced and results correctly render once the API resolves.
6. **`MovieCarousel.test.tsx` (Conditional Rendering & Interaction Test)**
   * **Why**: Handles horizontal scrolling and skeleton loaders. Ensures skeleton UI renders during loading and scroll buttons fire correct events.
7. **`AuthModal.test.tsx` (User Interaction & Form State Test)**
   * **Why**: Manages complex form state. Validates users can toggle between login/register, type into inputs, and trigger context methods.

### Backend Tests (Django)
1. **User Interactions & Watchlist Models (`recommendations/tests.py`)**
   * **Why**: Core to the app's functionality. Ensures data integrity, unique constraints (e.g., cannot add the same movie to a watchlist twice), and correct ordering.
2. **Recommendation API Endpoints (`recommendations/tests.py`)**
   * **Why**: To secure user data and validate CRUD operations. Tests verify unauthenticated rejections, successful data creation, and proper dashboard aggregation logic.
3. **Recommendation Engine (`recommendations/tests.py`)**
   * **Why**: The app's core intellectual property. Tests ensure mathematical accuracy when computing normalized genre weights and fallback behavior (trending movies) for new users.

---

## 2. What remains untested and what risks those gaps pose

While we have strong unit and integration coverage, several areas remain untested which pose potential risks:

### Frontend Gaps
1. **End-to-End (E2E) User Flows**
   * **Untested**: Full browser flows (e.g., Playwright/Cypress) simulating login, search, adding to watchlist, and dashboard viewing.
   * **Risk**: Isolated components work in Jest, but global state or routing glue might fail in a real browser.
2. **Error Boundaries & Network Failures**
   * **Untested**: UI behavior during `500 Internal Server Errors` or offline status.
   * **Risk**: The app might hang on infinite spinners or crash to a white screen instead of showing a graceful error message.
3. **Complex Compare Page State**
   * **Untested**: The `ComparePage` state swapping logic (swapping Movie A and B, computing percentages).
   * **Risk**: Future code changes could introduce regressions where swapping movies overwrites data or crashes the comparison math.

### Backend Gaps
1. **Performance/Load Testing**
   * **Untested**: How the `RecommendationEngine` and dashboard endpoints handle power users with 10,000+ interactions.
   * **Risk**: N+1 query bottlenecks could slow down the dashboard and cause API timeouts under heavy load.
2. **External API Resiliency (TMDB)**
   * **Untested**: Backend behavior when the external TMDB API rate-limits the server or goes down completely.
   * **Risk**: Cascading failures. If TMDB fails, our backend might crash instead of serving cached data or graceful fallback recommendations.

---

## 3. How to Run the Tests

### Running Frontend Tests
```bash
cd frontend
npm run test
# Or to run in watch mode:
npm run test:watch
```

### Expected Frontend Results
```text
 PASS  Frontend_tests/HeroSection.test.tsx
 PASS  Frontend_tests/Navbar.test.tsx
 PASS  Frontend_tests/HomePage.test.tsx
 PASS  Frontend_tests/MovieCard.test.tsx
 PASS  Frontend_tests/SearchModal.test.tsx
 PASS  Frontend_tests/MovieCarousel.test.tsx
 PASS  Frontend_tests/AuthModal.test.tsx

Test Suites: 7 passed, 7 total
Tests:       14 passed, 14 total
Snapshots:   0 total
Time:        2.845 s
```