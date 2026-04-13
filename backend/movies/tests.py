from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

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
            release_date="1999-10-15", vote_average=8.4,
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
            release_date="1999-10-15", vote_average=8.4, popularity=50.0
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
