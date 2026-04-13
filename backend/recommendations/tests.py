from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

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
