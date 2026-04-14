"""Tests for movies app views — search, mood, discover, and utility functions."""
from datetime import date
from unittest.mock import patch, MagicMock

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from movies.models import Genre, Movie, Person
from movies.views import safe_int, MOOD_MAP


class SafeIntTest(TestCase):
    """Tests for the safe_int utility function."""

    def test_valid_integer_string(self):
        self.assertEqual(safe_int("5"), 5)

    def test_none_returns_default(self):
        self.assertEqual(safe_int(None), 1)

    def test_empty_string_returns_default(self):
        self.assertEqual(safe_int(""), 1)

    def test_non_numeric_returns_default(self):
        self.assertEqual(safe_int("abc"), 1)

    def test_custom_default(self):
        self.assertEqual(safe_int("abc", default=10), 10)

    def test_float_string_returns_default(self):
        self.assertEqual(safe_int("3.5"), 1)


class MoodMapTest(TestCase):
    """Tests for the MOOD_MAP configuration."""

    def test_all_moods_have_required_keys(self):
        required = {"label", "description", "genres", "sort_by"}
        for slug, mood in MOOD_MAP.items():
            for key in required:
                self.assertIn(key, mood, f"Mood '{slug}' missing key '{key}'")

    def test_mood_slugs_are_valid(self):
        for slug in MOOD_MAP:
            self.assertTrue(slug.replace("-", "").isalpha(),
                            f"Invalid slug: {slug}")

    def test_minimum_moods_present(self):
        self.assertGreaterEqual(len(MOOD_MAP), 5)


class MoodListAPITest(APITestCase):
    """Tests for the mood list endpoint."""

    def test_mood_list_returns_all_moods(self):
        response = self.client.get("/api/movies/moods/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(MOOD_MAP))

    def test_mood_list_structure(self):
        response = self.client.get("/api/movies/moods/")
        for mood in response.data:
            self.assertIn("slug", mood)
            self.assertIn("label", mood)
            self.assertIn("description", mood)

    def test_mood_list_contains_cozy_night(self):
        response = self.client.get("/api/movies/moods/")
        slugs = [m["slug"] for m in response.data]
        self.assertIn("cozy-night", slugs)

    def test_mood_list_contains_adrenaline(self):
        response = self.client.get("/api/movies/moods/")
        slugs = [m["slug"] for m in response.data]
        self.assertIn("adrenaline", slugs)


class MoodMoviesAPITest(APITestCase):
    """Tests for the mood movies endpoint."""

    def test_invalid_mood_returns_404(self):
        response = self.client.get("/api/movies/moods/nonexistent-mood/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("movies.views.tmdb")
    def test_valid_mood_returns_movies(self, mock_tmdb):
        mock_tmdb.discover_movies.return_value = {
            "results": [{"id": 1, "title": "Test Movie"}],
            "total_pages": 1,
        }
        response = self.client.get("/api/movies/moods/cozy-night/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mood", response.data)
        self.assertEqual(response.data["mood"]["slug"], "cozy-night")


class SearchMoviesAPITest(APITestCase):
    """Tests for the movie search endpoint."""

    def test_search_requires_query(self):
        response = self.client.get("/api/movies/search/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_empty_query_returns_400(self):
        response = self.client.get("/api/movies/search/?q=")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("movies.views.tmdb")
    def test_search_with_valid_query(self, mock_tmdb):
        mock_tmdb.search_movies.return_value = {
            "results": [
                {"id": 550, "title": "Fight Club", "overview": "",
                 "release_date": "1999-10-15", "vote_average": 8.4,
                 "vote_count": 25000, "popularity": 50.0,
                 "poster_path": "/fc.jpg", "backdrop_path": "/fc_bg.jpg",
                 "genre_ids": [28]}
            ],
            "total_pages": 1,
            "total_results": 1,
        }
        response = self.client.get("/api/movies/search/?q=fight+club")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["query"], "fight club")


class CompareMoviesDetailAPITest(APITestCase):
    """Additional tests for movie comparison endpoint."""

    def test_compare_non_numeric_ids(self):
        response = self.client.get("/api/movies/compare/?ids=abc,xyz")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compare_single_id(self):
        response = self.client.get("/api/movies/compare/?ids=550")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compare_empty_string(self):
        response = self.client.get("/api/movies/compare/?ids=")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PersonViewSetAPITest(APITestCase):
    """Tests for the people API endpoints."""

    def setUp(self):
        self.person = Person.objects.create(
            tmdb_id=525, name="Christopher Nolan",
            profile_path="/nolan.jpg", known_for_department="Directing"
        )

    def test_list_people(self):
        response = self.client.get("/api/movies/people/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_person_detail(self):
        response = self.client.get(f"/api/movies/people/{self.person.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Christopher Nolan")

    def test_person_detail_includes_filmography(self):
        response = self.client.get(f"/api/movies/people/{self.person.pk}/")
        self.assertIn("directed_movies", response.data)
        self.assertIn("acted_movies", response.data)

    def test_person_not_found(self):
        response = self.client.get("/api/movies/people/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GenreMoviesAPITest(APITestCase):
    """Tests for genre-based movie listing endpoint."""

    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        # Create 25 movies so local DB path is used (>= 20)
        for i in range(25):
            m = Movie.objects.create(
                tmdb_id=i + 100, title=f"Action Movie {i}",
                popularity=100 - i,
            )
            m.genres.add(self.genre)

    def test_genre_movies_local_db(self):
        """When enough local movies exist, uses local DB instead of TMDB API."""
        response = self.client.get(f"/api/movies/genres/{self.genre.slug}/movies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
