from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from movies.services.tmdb_service import TMDBService, MovieSyncService, WikipediaService

from .models import Genre, Person, Movie, MovieCast, WatchProvider


class GenreModelTest(TestCase):
    """Tests for the Genre model."""

    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")

    def test_genre_str(self):
        self.assertEqual(str(self.genre), "Action")

    def test_genre_ordering(self):
        Genre.objects.create(tmdb_id=35, name="Comedy", slug="comedy")
        genres = list(Genre.objects.values_list("name", flat=True))
        self.assertEqual(genres, ["Action", "Comedy"])


class PersonModelTest(TestCase):
    """Tests for the Person model."""

    def setUp(self):
        self.person = Person.objects.create(
            tmdb_id=1, name="Christopher Nolan",
            profile_path="/nolan.jpg", known_for_department="Directing"
        )

    def test_person_str(self):
        self.assertEqual(str(self.person), "Christopher Nolan")

    def test_profile_url(self):
        self.assertIn("/w185/nolan.jpg", self.person.profile_url)

    def test_profile_url_empty(self):
        self.person.profile_path = ""
        self.assertIsNone(self.person.profile_url)


class MovieModelTest(TestCase):
    """Tests for the Movie model."""

    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=550, title="Fight Club",
            release_date=date(1999, 10, 15), vote_average=8.4,
            popularity=50.0, poster_path="/fightclub.jpg",
            backdrop_path="/fightclub_bg.jpg", trailer_key="SUXWAEX2jlg"
        )

    def test_movie_str(self):
        self.assertEqual(str(self.movie), "Fight Club (1999)")

    def test_poster_url(self):
        self.assertIn("/w500/fightclub.jpg", self.movie.poster_url)

    def test_backdrop_url(self):
        self.assertIn("/w1280/fightclub_bg.jpg", self.movie.backdrop_url)

    def test_trailer_url(self):
        self.assertIn("youtube.com/watch?v=SUXWAEX2jlg", self.movie.trailer_url)

    def test_trailer_embed_url(self):
        self.assertIn("youtube.com/embed/SUXWAEX2jlg", self.movie.trailer_embed_url)


class GenreAPITest(APITestCase):
    """Tests for the genres API endpoints."""

    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")

    def test_list_genres(self):
        response = self.client.get("/api/movies/genres/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_genre_detail_by_slug(self):
        response = self.client.get(f"/api/movies/genres/{self.genre.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Action")


class MovieAPITest(APITestCase):
    """Tests for the movies API endpoints."""

    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        self.movie = Movie.objects.create(
            tmdb_id=550, title="Fight Club",
            release_date=date(1999, 10, 15), vote_average=8.4, popularity=50.0
        )
        self.movie.genres.add(self.genre)

    def test_list_movies(self):
        response = self.client.get("/api/movies/list/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_movie_detail(self):
        response = self.client.get(f"/api/movies/list/{self.movie.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Fight Club")

    def test_mood_list(self):
        response = self.client.get("/api/movies/moods/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        slugs = [m["slug"] for m in response.data]
        self.assertIn("cozy-night", slugs)


class CompareMoviesAPITest(APITestCase):
    """Tests for movie comparison endpoint."""

    def test_compare_requires_two_ids(self):
        response = self.client.get("/api/movies/compare/?ids=550")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compare_no_ids(self):
        response = self.client.get("/api/movies/compare/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

FAKE_MOVIE_PAYLOAD = {
    "id": 550, "imdb_id": "tt0137523",
    "title": "Fight Club", "original_title": "Fight Club",
    "overview": "An insomniac office worker…", "tagline": "Mischief. Mayhem. Soap.",
    "release_date": "1999-10-15", "runtime": 139,
    "vote_average": 8.4, "vote_count": 25000, "popularity": 50.0,
    "poster_path": "/fc.jpg", "backdrop_path": "/fc_bg.jpg",
    "budget": 63000000, "revenue": 101200000,
    "status": "Released", "homepage": "",
    "genres": [{"id": 28, "name": "Action"}, {"id": 18, "name": "Drama"}],
    "credits": {
        "crew": [
            {"id": 7467, "name": "David Fincher", "job": "Director",
             "profile_path": "/fincher.jpg", "known_for_department": "Directing"},
            {"id": 100, "name": "Some Producer", "job": "Producer",
             "profile_path": "", "known_for_department": "Production"},
        ],
        "cast": [
            {"id": 819, "name": "Edward Norton", "character": "The Narrator",
             "profile_path": "/norton.jpg", "known_for_department": "Acting"},
            {"id": 287, "name": "Brad Pitt", "character": "Tyler Durden",
             "profile_path": "/pitt.jpg", "known_for_department": "Acting"},
        ],
    },
    "videos": {
        "results": [
            {"site": "YouTube", "type": "Trailer", "key": "SUXWAEX2jlg"},
            {"site": "YouTube", "type": "Teaser", "key": "OTHER"},
        ]
    },
    "watch/providers": {
        "results": {
            "US": {
                "link": "https://www.themoviedb.org/movie/550/watch",
                "flatrate": [{"provider_name": "Netflix", "logo_path": "/nf.jpg"}],
            }
        }
    },
}

class MovieSyncServiceTest(TestCase):
    """Verify the TMDB→local-DB sync pipeline creates all related objects."""

    @patch.object(TMDBService, "get_movie_details")
    def test_sync_movie_creates_all_related_models(self, mock_details):
        mock_details.return_value = FAKE_MOVIE_PAYLOAD
        movie = MovieSyncService().sync_movie(550)

        # Core movie fields
        self.assertIsNotNone(movie)
        self.assertEqual(movie.title, "Fight Club")
        self.assertEqual(movie.tmdb_id, 550)
        self.assertEqual(movie.runtime, 139)

        # Genres
        self.assertEqual(movie.genres.count(), 2)
        self.assertTrue(movie.genres.filter(name="Action").exists())

        # Directors — only the crew member with job=="Director" is linked
        self.assertEqual(movie.directors.count(), 1)
        self.assertEqual(movie.directors.first().name, "David Fincher")

        # Cast through model
        casts = MovieCast.objects.filter(movie=movie).order_by("order")
        self.assertEqual(casts.count(), 2)
        self.assertEqual(casts.first().character, "The Narrator")

        # Trailer (picks first YouTube Trailer, not the Teaser)
        self.assertEqual(movie.trailer_key, "SUXWAEX2jlg")

        # Watch providers
        providers = WatchProvider.objects.filter(movie=movie)
        self.assertEqual(providers.count(), 1)
        self.assertEqual(providers.first().provider_name, "Netflix")

class WikipediaServiceTest(TestCase):
    """Verify Wikipedia enrichment succeeds and falls back on 404."""

    @patch("movies.services.tmdb_service.requests.get")
    @patch("movies.services.tmdb_service.cache")
    def test_summary_fetched_and_fallback_on_404(self, mock_cache, mock_get):
        mock_cache.get.return_value = None  # no cache

        # First call (year-specific) returns 404, second (generic) returns 200
        resp_404 = MagicMock(status_code=404)
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {
            "extract": "Fight Club is a 1999 American film…",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Fight_Club_(film)"}},
            "thumbnail": {"source": "https://upload.wikimedia.org/thumb.jpg"},
        }
        mock_get.side_effect = [resp_404, resp_200]

        result = WikipediaService.get_movie_summary("Fight Club", year=1999)

        self.assertIn("1999 American film", result["summary"])
        self.assertIn("wikipedia.org", result["url"])
        self.assertEqual(mock_get.call_count, 2)

class DiscoverFilteredAPITest(APITestCase):
    """Test the /api/movies/discover/ endpoint with multiple filters."""

    @patch("movies.views.tmdb")
    def test_filters_forwarded_and_response_structured(self, mock_tmdb):
        mock_tmdb.discover_movies.return_value = {
            "results": [
                {"id": 1, "title": "Filtered Movie", "overview": "",
                 "release_date": "2020-06-15", "vote_average": 7.5,
                 "vote_count": 300, "popularity": 40.0,
                 "poster_path": "/m.jpg", "backdrop_path": None}
            ],
            "total_pages": 1,
            "total_results": 1,
        }

        response = self.client.get(
            "/api/movies/discover/",
            {"genre": "28", "year_from": "2020", "year_to": "2023",
             "rating_min": "7", "sort": "vote_average.desc"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["page"], 1)

        call_kwargs = mock_tmdb.discover_movies.call_args[1]
        self.assertEqual(call_kwargs["with_genres"], "28")
        self.assertEqual(call_kwargs["primary_release_date.gte"], "2020-01-01")
        self.assertEqual(call_kwargs["primary_release_date.lte"], "2023-12-31")
        self.assertEqual(call_kwargs["vote_average.gte"], 7.0)
        self.assertEqual(call_kwargs["sort_by"], "vote_average.desc")

class TrendingMoviesAPITest(APITestCase):
    """Test the /api/movies/trending/ endpoint."""

    @patch("movies.views.tmdb")
    def test_trending_returns_results_with_window(self, mock_tmdb):
        mock_tmdb.get_trending_movies.return_value = {
            "results": [
                {"id": 10, "title": "Trending Today", "overview": "",
                 "release_date": "2025-01-01", "vote_average": 8.0,
                 "vote_count": 5000, "popularity": 120.0,
                 "poster_path": "/t.jpg", "backdrop_path": "/tb.jpg"},
            ],
            "total_pages": 5,
        }

        response = self.client.get("/api/movies/trending/?window=day")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["page"], 1)

        mock_tmdb.get_trending_movies.assert_called_once_with(
            time_window="day", page=1,
        )
