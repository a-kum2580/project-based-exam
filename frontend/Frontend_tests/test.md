# Frontend Testing Documentation

This document outlines the testing strategy, the suites we have implemented for the CineQuest frontend, and instructions on how to run them.

## What Tests We Did & Why

1. **`HeroSection.test.tsx` (Component/Safety Test)**
   * **Why**: To prevent runtime crashes. We previously had a bug where the API returned `undefined` instead of an array, causing `.slice is not a function`. This test ensures the component gracefully falls back to a safe UI if invalid props are passed.

2. **`Navbar.test.tsx` (Integration/Auth Test)**
   * **Why**: Authentication state dictates the main navigation. By mocking the `useAuth` context, we ensure that unauthenticated users see the "Sign In" button, while authenticated users see their Avatar and "Dashboard" links.

3. **`HomePage.test.tsx` (Async Data Fetching Test)**
   * **Why**: The home page coordinates multiple API calls (`trending`, `nowPlaying`, `topRated`). This test mocks those endpoints to ensure the page doesn't crash during the loading phase and properly renders all child components once data is resolved.

4. **`MovieCard.test.tsx` (Unit/Prop Logic Test)**
   * **Why**: The `MovieCard` is reused heavily throughout the app. This test ensures conditional logic (like hiding the overview text unless `showOverview=true` or displaying the rating badge only if the vote average is > 0) functions exactly as expected.

5. **`SearchModal.test.tsx` (Integration/Debounce Test)**
   * **Why**: Search functionality is complex due to debouncing and API interactions. We wrote this test to ensure that typing quickly doesn't spam the API, and that the results correctly render in the modal after the mocked `moviesAPI.search` resolves.

---

## How to Run the Tests

To run the test suite, open your terminal, navigate to the `frontend` directory, and use the npm scripts defined in `package.json`.

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Run the tests once
npm run test

# 3. (Optional) Run tests in watch mode while developing
npm run test:watch
```

6. **`MovieCarousel.test.tsx` (Conditional Rendering & Interaction Test)**
   * **Why**: The carousel handles horizontal scrolling and displays skeleton loaders during data fetching. This test ensures the skeleton UI renders correctly when `loading=true` and verifies the left/right scroll buttons fire the correct `scrollBy` events.

7. **`AuthModal.test.tsx` (User Interaction & Form State Test)**
   * **Why**: The authentication modal manages complex form state (toggling between login and register). This test validates that users can type into the inputs, switch modes to reveal the email field, and trigger the correct context methods (`login` vs `register`).

---

## Expected Results

When running `npm run test`, Jest will discover all files ending in `.test.tsx` and execute them using the JSDOM environment. You should see an output similar to this indicating total success:

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
Ran all test suites.
```