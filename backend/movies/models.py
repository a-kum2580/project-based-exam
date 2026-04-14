from django.db import models
from django.conf import settings

class TMDBImageService:
    """Centralized image URL builder (avoids duplication)."""

    @staticmethod
    def build(path: str, size: str) -> str | None:
        if path:
            return f"{settings.TMDB_IMAGE_BASE_URL}/{size}{path}"
        return None


class YouTubeService:
    """Centralized YouTube URL builder."""

    @staticmethod
    def watch_url(key: str) -> str | None:
        if key:
            return f"https://www.youtube.com/watch?v={key}"
        return None

    @staticmethod
    def embed_url(key: str) -> str | None:
        if key:
            return f"https://www.youtube.com/embed/{key}"
        return None


class Genre(models.Model):
    """Movie genre synced from TMDB."""

    tmdb_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Person(models.Model):
    """Director, actor, or crew member."""

    class Role(models.TextChoices):
        DIRECTOR = "director", "Director"
        ACTOR = "actor", "Actor"
        WRITER = "writer", "Writer"
        PRODUCER = "producer", "Producer"

    tmdb_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    profile_path = models.CharField(max_length=255, blank=True, default="")
    biography = models.TextField(blank=True, default="")
    birthday = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=255, blank=True, default="")
    known_for_department = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "People"

    def __str__(self):
        return self.name

    @property
    def profile_url(self):
        return TMDBImageService.build(self.profile_path, "w185")


class Movie(models.Model):
    """Movie cached from TMDB with enrichment."""

    tmdb_id = models.IntegerField(unique=True, db_index=True)
    imdb_id = models.CharField(max_length=20, blank=True, default="", db_index=True)
    title = models.CharField(max_length=500)
    original_title = models.CharField(max_length=500, blank=True, default="")
    overview = models.TextField(blank=True, default="")
    tagline = models.CharField(max_length=500, blank=True, default="")
    release_date = models.DateField(null=True, blank=True)
    runtime = models.IntegerField(null=True, blank=True)
    vote_average = models.FloatField(default=0)
    vote_count = models.IntegerField(default=0)
    popularity = models.FloatField(default=0)
    poster_path = models.CharField(max_length=255, blank=True, default="")
    backdrop_path = models.CharField(max_length=255, blank=True, default="")
    budget = models.BigIntegerField(default=0)
    revenue = models.BigIntegerField(default=0)
    status = models.CharField(max_length=50, blank=True, default="")
    homepage = models.URLField(max_length=500, blank=True, default="")

    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    directors = models.ManyToManyField(Person, related_name="directed_movies", blank=True)
    cast = models.ManyToManyField(Person, through="MovieCast", related_name="acted_movies", blank=True)

    trailer_key = models.CharField(max_length=50, blank=True, default="")
    wikipedia_url = models.URLField(max_length=500, blank=True, default="")
    wikipedia_summary = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-popularity"]
        indexes = [
            models.Index(fields=["-vote_average", "-vote_count"]),
            models.Index(fields=["-popularity"]),
            models.Index(fields=["release_date"]),
        ]

    def __str__(self):
        year = self.release_date.year if self.release_date else "N/A"
        return f"{self.title} ({year})"

    @property
    def poster_url(self):
        return TMDBImageService.build(self.poster_path, "w500")

    @property
    def poster_url_small(self):
        return TMDBImageService.build(self.poster_path, "w185")

    @property
    def backdrop_url(self):
        return TMDBImageService.build(self.backdrop_path, "w1280")

    @property
    def trailer_url(self):
        return YouTubeService.watch_url(self.trailer_key)

    @property
    def trailer_embed_url(self):
        return YouTubeService.embed_url(self.trailer_key)


class MovieCast(models.Model):
    """Through model for Movie-Person cast relationship."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    character = models.CharField(max_length=500, blank=True, default="")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = ["movie", "person", "character"]

    def __str__(self):
        return f"{self.person.name} as {self.character} in {self.movie.title}"


class WatchProvider(models.Model):
    """Streaming/rental/purchase providers."""

    class ProviderType(models.TextChoices):
        STREAM = "stream", "Streaming"
        RENT = "rent", "Rent"
        BUY = "buy", "Buy"
        FREE = "free", "Free"

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="watch_providers")
    provider_name = models.CharField(max_length=200)
    provider_type = models.CharField(max_length=10, choices=ProviderType.choices)
    logo_path = models.CharField(max_length=255, blank=True, default="")
    link = models.URLField(max_length=500, blank=True, default="")
    country_code = models.CharField(max_length=5, default="US")

    class Meta:
        ordering = ["provider_type", "provider_name"]

    def __str__(self):
        return f"{self.provider_name} ({self.provider_type}) - {self.movie.title}"

    @property
    def logo_url(self):
        return TMDBImageService.build(self.logo_path, "w92")
