from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from movies.models import Genre
from movies.services.tmdb_service import TMDBService
from recommendations.services.engine import RecommendationEngine

from .models import UserMovieInteraction, UserGenrePreference, Watchlist

User = get_user_model()


class InteractionModelTest(TestCase):
    """Tests for UserMovieInteraction model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.interaction = UserMovieInteraction.objects.create(
            user=self.user, movie_tmdb_id=550, movie_title="Fight Club",
            interaction_type="like", genre_ids=[28, 18]
        )

    def test_interaction_str(self):
        self.assertIn("testuser", str(self.interaction))
        self.assertIn("like", str(self.interaction))

    def test_interaction_ordering(self):
        """Most recent first."""
        newer = UserMovieInteraction.objects.create(
            user=self.user, movie_tmdb_id=680, movie_title="Pulp Fiction",
            interaction_type="watched", genre_ids=[53, 80]
        )
        interactions = list(UserMovieInteraction.objects.filter(user=self.user))
        self.assertEqual(interactions[0], newer)


class WatchlistModelTest(TestCase):
    """Tests for Watchlist model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_add_to_watchlist(self):
        item = Watchlist.objects.create(
            user=self.user, movie_tmdb_id=550, movie_title="Fight Club"
        )
        self.assertFalse(item.watched)
        self.assertIsNone(item.watched_at)

    def test_watchlist_unique_constraint(self):
        """Cannot add same movie twice for same user."""
        Watchlist.objects.create(
            user=self.user, movie_tmdb_id=550, movie_title="Fight Club"
        )
        with self.assertRaises(Exception):
            Watchlist.objects.create(
                user=self.user, movie_tmdb_id=550, movie_title="Fight Club"
            )


class TrackInteractionAPITest(APITestCase):
    """Tests for interaction tracking endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    def test_track_like(self):
        data = {
            "movie_tmdb_id": 550,
            "movie_title": "Fight Club",
            "interaction_type": "like",
            "genre_ids": [28, 18],
        }
        response = self.client.post("/api/recommendations/track/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserMovieInteraction.objects.count(), 1)

    def test_track_unauthenticated(self):
        self.client.force_authenticate(user=None)
        data = {"movie_tmdb_id": 550, "movie_title": "Fight Club", "interaction_type": "like"}
        response = self.client.post("/api/recommendations/track/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WatchlistAPITest(APITestCase):
    """Tests for watchlist CRUD endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    def test_add_to_watchlist(self):
        data = {"movie_tmdb_id": 550, "movie_title": "Fight Club", "poster_path": "/fc.jpg"}
        response = self.client.post("/api/recommendations/watchlist/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_watchlist(self):
        Watchlist.objects.create(user=self.user, movie_tmdb_id=550, movie_title="Fight Club")
        response = self.client.get("/api/recommendations/watchlist/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_watchlist_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/recommendations/watchlist/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_watchlist_returns_400(self):
        """Adding same movie twice should return 400 not 500."""
        data = {"movie_tmdb_id": 550, "movie_title": "Fight Club"}
        self.client.post("/api/recommendations/watchlist/", data, format="json")
        response = self.client.post("/api/recommendations/watchlist/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GenrePreferencesAPITest(APITestCase):
    """Tests for the genre preferences endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    def test_preferences_empty(self):
        response = self.client.get("/api/recommendations/preferences/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DashboardAPITest(APITestCase):
    """Tests for the dashboard stats endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    def test_dashboard_empty_user(self):
        response = self.client.get("/api/recommendations/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", response.data)
        self.assertEqual(response.data["summary"]["total_interactions"], 0)

    def test_dashboard_with_interactions(self):
        UserMovieInteraction.objects.create(
            user=self.user, movie_tmdb_id=550, movie_title="Fight Club",
            interaction_type="like", genre_ids=[28]
        )
        response = self.client.get("/api/recommendations/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["likes"], 1)


class BecauseYouWatchedAPITest(APITestCase):
    """Tests for the because-you-watched endpoint response shaping."""

    def setUp(self):
        self.user = User.objects.create_user(username="watchuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    @patch("recommendations.views.get_recommendation_engine")
    def test_because_you_watched_serializes_nested_movie_groups(self, mock_get_engine):
        mock_engine = MagicMock()
        mock_engine.get_because_you_watched.return_value = {
            "Fight Club": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "overview": "",
                    "release_date": "1999-10-15",
                    "vote_average": 8.4,
                    "vote_count": 25000,
                    "popularity": 50.0,
                    "poster_path": "/fc.jpg",
                    "backdrop_path": "/fc_bg.jpg",
                }
            ]
        }
        mock_get_engine.return_value = mock_engine

        response = self.client.get("/api/recommendations/because-you-watched/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Fight Club", response.data)
        self.assertEqual(response.data["Fight Club"][0]["title"], "Fight Club")
        mock_engine.get_because_you_watched.assert_called_once_with(self.user)

class RecommendationEnginePreferencesTest(TestCase):
    """Verify the engine computes normalised genre weights from interactions."""

    def setUp(self):
        self.user = User.objects.create_user(username="recuser", password="pass12345")
        Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        Genre.objects.create(tmdb_id=18, name="Drama", slug="drama")

        # Two "like" interactions (weight 5 each) for Action  → total 10
        # One "view" interaction (weight 1) for Drama          → total  1
        UserMovieInteraction.objects.create(
            user=self.user, movie_tmdb_id=1, movie_title="Movie A",
            interaction_type="like", genre_ids=[28],
        )
        UserMovieInteraction.objects.create(
            user=self.user, movie_tmdb_id=2, movie_title="Movie B",
            interaction_type="like", genre_ids=[28],
        )
        UserMovieInteraction.objects.create(
            user=self.user, movie_tmdb_id=3, movie_title="Movie C",
            interaction_type="view", genre_ids=[18],
        )

    def test_genre_weights_normalised_correctly(self):
        engine = RecommendationEngine()
        prefs = engine.compute_genre_preferences(self.user)

        # prefs is a list of (genre_id, normalised_score) sorted desc
        pref_dict = dict(prefs)

        # Action had raw score 10 → should normalise to 100 (max)
        self.assertEqual(pref_dict[28], 100.0)

        # Drama had raw score 1 → (1/10)*100 = 10.0
        self.assertEqual(pref_dict[18], 10.0)

        # Verify DB records were saved
        db_pref = UserGenrePreference.objects.get(user=self.user, genre_tmdb_id=28)
        self.assertEqual(db_pref.weight, 100.0)
        self.assertEqual(db_pref.genre_name, "Action")

class RecommendationEngineNewUserTest(TestCase):
    """A user with zero interactions should receive trending movies."""

    def setUp(self):
        self.user = User.objects.create_user(username="newuser", password="pass12345")

    @patch.object(TMDBService, "get_trending_movies")
    def test_new_user_gets_trending_fallback(self, mock_trending):
        mock_trending.return_value = {
            "results": [
                {"id": 100, "title": "Trending A"},
                {"id": 200, "title": "Trending B"},
            ]
        }
        engine = RecommendationEngine()
        movies = engine.get_recommendations(self.user)

        self.assertEqual(len(movies), 2)
        self.assertEqual(movies[0]["title"], "Trending A")
        mock_trending.assert_called_once()


class RecommendationEngineBoundaryTest(TestCase):
    """Boundary coverage for recommendation fallback and top-genre handling."""

    def setUp(self):
        self.user = User.objects.create_user(username="edgeuser", password="pass12345")

    @patch.object(RecommendationEngine, "compute_genre_preferences")
    @patch.object(TMDBService, "get_trending_movies")
    def test_empty_top_genres_falls_back_to_trending(self, mock_trending, mock_compute):
        mock_compute.return_value = []
        mock_trending.return_value = {"results": [{"id": 1, "title": "Fallback Movie"}]}

        engine = RecommendationEngine()
        movies = engine.get_recommendations(self.user, page=1)

        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["title"], "Fallback Movie")
        mock_trending.assert_called_once_with(page=1)

    @patch.object(TMDBService, "discover_movies")
    @patch.object(RecommendationEngine, "compute_genre_preferences")
    def test_single_preference_genre_works(self, mock_compute, mock_discover):
        mock_compute.return_value = [(28, 100.0)]
        mock_discover.return_value = {
            "results": [{"id": 10, "title": "Action Pick", "vote_average": 8.0}],
        }

        engine = RecommendationEngine()
        movies = engine.get_recommendations(self.user, page=1)

        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["title"], "Action Pick")
        mock_discover.assert_called_once()

    @patch.object(TMDBService, "discover_movies")
    @patch.object(RecommendationEngine, "compute_genre_preferences")
    def test_recommendations_deduplicate_seen_and_repeat_movies(self, mock_compute, mock_discover):
        mock_compute.return_value = [(28, 100.0)]
        mock_discover.return_value = {
            "results": [
                {"id": 200, "title": "Seen Movie", "vote_average": 9.5},
                {"id": 201, "title": "Unique Movie", "vote_average": 8.0},
                {"id": 201, "title": "Unique Movie", "vote_average": 8.0},
                {"id": 202, "title": "Second Movie", "vote_average": 7.0},
            ],
        }
        UserMovieInteraction.objects.create(
            user=self.user,
            movie_tmdb_id=200,
            movie_title="Seen Movie",
            interaction_type="watched",
            genre_ids=[28],
        )

        engine = RecommendationEngine()
        movies = engine.get_recommendations(self.user, page=1, limit=10)

        movie_ids = [movie["id"] for movie in movies]
        self.assertEqual(movie_ids, [201, 202])
        self.assertNotIn(200, movie_ids)
        self.assertTrue(all("_recommendation_score" not in movie for movie in movies))


class RecommendationEnginePolicyInjectionTest(TestCase):
    """Engine should honor injected interaction-weight policies."""

    class _CustomPolicy:
        def weight_for(self, interaction_type: str) -> float:
            if interaction_type == "like":
                return 10.0
            if interaction_type == "view":
                return 1.0
            return 1.0

    def setUp(self):
        self.user = User.objects.create_user(username="policyuser", password="pass12345")
        Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        Genre.objects.create(tmdb_id=18, name="Drama", slug="drama")

        UserMovieInteraction.objects.create(
            user=self.user,
            movie_tmdb_id=11,
            movie_title="Movie Like",
            interaction_type="like",
            genre_ids=[28],
        )
        UserMovieInteraction.objects.create(
            user=self.user,
            movie_tmdb_id=12,
            movie_title="Movie View",
            interaction_type="view",
            genre_ids=[18],
        )

    def test_custom_weight_policy_changes_normalized_scores(self):
        engine = RecommendationEngine(weight_policy=self._CustomPolicy())
        prefs = dict(engine.compute_genre_preferences(self.user))

        self.assertEqual(prefs[28], 100.0)
        self.assertEqual(prefs[18], 10.0)
