"""Tests for movies app serializers."""
from datetime import date

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from movies.models import Genre, Person, Movie, MovieCast, WatchProvider
from movies.serializers import (
    GenreSerializer,
    PersonCompactSerializer,
    PersonDetailSerializer,
    MovieCompactSerializer,
    MovieDetailSerializer,
    MovieCastSerializer,
    WatchProviderSerializer,
    TMDBMovieSerializer,
)


class GenreSerializerTest(TestCase):
    """Tests for GenreSerializer."""

    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        Movie.objects.create(tmdb_id=1, title="Movie 1", popularity=10).genres.add(self.genre)
        Movie.objects.create(tmdb_id=2, title="Movie 2", popularity=5).genres.add(self.genre)

    def test_serialized_fields(self):
        data = GenreSerializer(self.genre).data
        self.assertEqual(set(data.keys()), {"id", "tmdb_id", "name", "slug", "movie_count"})

    def test_movie_count(self):
        data = GenreSerializer(self.genre).data
        self.assertEqual(data["movie_count"], 2)

    def test_movie_count_zero(self):
        empty_genre = Genre.objects.create(tmdb_id=99, name="Empty", slug="empty")
        data = GenreSerializer(empty_genre).data
        self.assertEqual(data["movie_count"], 0)


class PersonCompactSerializerTest(TestCase):
    """Tests for PersonCompactSerializer."""

    def setUp(self):
        self.person = Person.objects.create(
            tmdb_id=1, name="Christopher Nolan",
            profile_path="/nolan.jpg", known_for_department="Directing"
        )

    def test_serialized_fields(self):
        data = PersonCompactSerializer(self.person).data
        self.assertEqual(data["name"], "Christopher Nolan")
        self.assertIn("profile_url", data)
        self.assertEqual(data["known_for_department"], "Directing")

    def test_profile_url_present(self):
        data = PersonCompactSerializer(self.person).data
        self.assertIn("/w185/nolan.jpg", data["profile_url"])

    def test_profile_url_none_when_empty(self):
        self.person.profile_path = ""
        self.person.save()
        data = PersonCompactSerializer(self.person).data
        self.assertIsNone(data["profile_url"])


class MovieCompactSerializerTest(TestCase):
    """Tests for MovieCompactSerializer (lightweight list view)."""

    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        self.movie = Movie.objects.create(
            tmdb_id=550, title="Fight Club",
            release_date=date(1999, 10, 15), vote_average=8.4,
            popularity=50.0, poster_path="/fc.jpg", runtime=139,
        )
        self.movie.genres.add(self.genre)

    def test_contains_expected_fields(self):
        data = MovieCompactSerializer(self.movie).data
        expected_fields = {
            "id", "tmdb_id", "title", "overview", "release_date", "year",
            "vote_average", "vote_count", "popularity", "poster_url",
            "poster_url_small", "genres", "runtime",
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_year_extraction(self):
        data = MovieCompactSerializer(self.movie).data
        self.assertEqual(data["year"], 1999)

    def test_year_none_when_no_release_date(self):
        self.movie.release_date = None
        self.movie.save()
        data = MovieCompactSerializer(self.movie).data
        self.assertIsNone(data["year"])

    def test_poster_urls(self):
        data = MovieCompactSerializer(self.movie).data
        self.assertIn("/w500/fc.jpg", data["poster_url"])
        self.assertIn("/w185/fc.jpg", data["poster_url_small"])

    def test_nested_genres(self):
        data = MovieCompactSerializer(self.movie).data
        self.assertEqual(len(data["genres"]), 1)
        self.assertEqual(data["genres"][0]["name"], "Action")


class MovieDetailSerializerTest(TestCase):
    """Tests for MovieDetailSerializer (full detail view)."""

    def setUp(self):
        self.genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        self.director = Person.objects.create(
            tmdb_id=525, name="Christopher Nolan",
            profile_path="/nolan.jpg", known_for_department="Directing"
        )
        self.actor = Person.objects.create(
            tmdb_id=819, name="Edward Norton",
            profile_path="/norton.jpg", known_for_department="Acting"
        )
        self.movie = Movie.objects.create(
            tmdb_id=550, title="Fight Club",
            release_date=date(1999, 10, 15), vote_average=8.4,
            popularity=50.0, poster_path="/fc.jpg",
            backdrop_path="/fc_bg.jpg", trailer_key="SUXWAEX2jlg",
            budget=63000000, revenue=101200000,
        )
        self.movie.genres.add(self.genre)
        self.movie.directors.add(self.director)
        MovieCast.objects.create(
            movie=self.movie, person=self.actor,
            character="The Narrator", order=0
        )

    def test_contains_all_detail_fields(self):
        data = MovieDetailSerializer(self.movie).data
        for field in ["trailer_url", "trailer_embed_url", "backdrop_url",
                       "directors", "cast", "watch_providers", "budget", "revenue"]:
            self.assertIn(field, data)

    def test_directors_populated(self):
        data = MovieDetailSerializer(self.movie).data
        self.assertEqual(len(data["directors"]), 1)
        self.assertEqual(data["directors"][0]["name"], "Christopher Nolan")

    def test_cast_populated(self):
        data = MovieDetailSerializer(self.movie).data
        self.assertEqual(len(data["cast"]), 1)
        self.assertEqual(data["cast"][0]["character"], "The Narrator")
        self.assertEqual(data["cast"][0]["person"]["name"], "Edward Norton")

    def test_trailer_urls(self):
        data = MovieDetailSerializer(self.movie).data
        self.assertIn("youtube.com/watch?v=SUXWAEX2jlg", data["trailer_url"])
        self.assertIn("youtube.com/embed/SUXWAEX2jlg", data["trailer_embed_url"])


class TMDBMovieSerializerTest(TestCase):
    """Tests for TMDBMovieSerializer (raw TMDB API response formatting)."""

    def test_basic_representation(self):
        raw = {
            "id": 550, "title": "Fight Club",
            "overview": "A movie about fighting",
            "release_date": "1999-10-15",
            "vote_average": 8.4, "vote_count": 25000,
            "popularity": 50.0,
            "poster_path": "/fc.jpg", "backdrop_path": "/fc_bg.jpg",
            "genre_ids": [28, 18],
        }
        data = TMDBMovieSerializer(raw).data
        self.assertEqual(data["title"], "Fight Club")
        self.assertEqual(data["year"], 1999)

    def test_poster_url_generated(self):
        raw = {
            "id": 550, "title": "Test",
            "overview": "", "release_date": "2020-01-01",
            "vote_average": 7.0, "vote_count": 100,
            "popularity": 10.0,
            "poster_path": "/test.jpg", "backdrop_path": None,
        }
        data = TMDBMovieSerializer(raw).data
        self.assertIn("/w500/test.jpg", data["poster_url"])
        self.assertIn("/w185/test.jpg", data["poster_url_small"])

    def test_year_none_when_empty_release_date(self):
        raw = {
            "id": 1, "title": "No Date",
            "overview": "", "release_date": "",
            "vote_average": 0, "vote_count": 0,
            "popularity": 0,
            "poster_path": None, "backdrop_path": None,
        }
        data = TMDBMovieSerializer(raw).data
        self.assertIsNone(data["year"])

    def test_no_poster_url_when_path_null(self):
        raw = {
            "id": 1, "title": "No Poster",
            "overview": "", "release_date": "2020-01-01",
            "vote_average": 0, "vote_count": 0,
            "popularity": 0,
            "poster_path": None, "backdrop_path": None,
        }
        data = TMDBMovieSerializer(raw).data
        self.assertNotIn("poster_url", data)


class WatchProviderSerializerTest(TestCase):
    """Tests for WatchProviderSerializer."""

    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=550, title="Fight Club", popularity=50.0
        )
        self.provider = WatchProvider.objects.create(
            movie=self.movie,
            provider_name="Netflix",
            provider_type="stream",
            logo_path="/netflix.jpg",
            link="https://netflix.com/watch/550",
        )

    def test_serialized_fields(self):
        data = WatchProviderSerializer(self.provider).data
        self.assertEqual(data["provider_name"], "Netflix")
        self.assertEqual(data["provider_type"], "stream")
        self.assertIn("/w92/netflix.jpg", data["logo_url"])

    def test_logo_url_none_when_empty(self):
        self.provider.logo_path = ""
        self.provider.save()
        data = WatchProviderSerializer(self.provider).data
        self.assertIsNone(data["logo_url"])
