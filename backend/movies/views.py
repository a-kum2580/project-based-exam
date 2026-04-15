import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend

from .models import Movie, Genre, Person
from .serializers import (
    MovieCompactSerializer, MovieDetailSerializer,
    GenreSerializer, PersonCompactSerializer, PersonDetailSerializer,
    TMDBMovieSerializer,
)
from .services.discovery_service import MovieDiscoveryService
from .services.tmdb_service import (
    TMDBService,
    MovieSyncService,
    WikipediaService,
    TMDBAPIError,
    MovieNotFoundError,
)

logger = logging.getLogger(__name__)
MAX_PAGE = 500


def get_tmdb_service() -> TMDBService:
    return TMDBService()


def get_movie_sync_service(tmdb_service: TMDBService | None = None) -> MovieSyncService:
    return MovieSyncService(tmdb_client=tmdb_service)


def get_discovery_service(tmdb_service: TMDBService) -> MovieDiscoveryService:
    return MovieDiscoveryService(tmdb_client=tmdb_service, cache_ttl=300, max_scan_pages=MAX_PAGE)


def _ensure_tmdb_ok(data: dict):
    """Raise a 502-style error when TMDB calls fail."""
    if isinstance(data, dict) and data.get("_error"):
        raise APIException(detail=data["_error"])


def safe_int(value, default=1):
    """Safely parse an integer from query params, returning default on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    """Safely parse a float from query params, returning default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_page(value, default=1, max_page=MAX_PAGE):
    """Parse page query params into a bounded positive page number."""
    page = safe_int(value, default=default)
    if page is None or page < 1:
        return default
    return min(page, max_page)

## Movie ViewSet
class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "directors").all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["genres__slug"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieCompactSerializer

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        movie = self.get_object()
        tmdb_service = get_tmdb_service()
        data = tmdb_service.get_movie_recommendations(movie.tmdb_id)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        movie = self.get_object()
        tmdb_service = get_tmdb_service()
        data = tmdb_service.get_similar_movies(movie.tmdb_id)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def wikipedia(self, request, pk=None):
        movie = self.get_object()
        year = movie.release_date.year if movie.release_date else None
        wiki_data = WikipediaService.get_movie_summary(movie.title, year)

        return Response(wiki_data)


## Genre ViewSet
class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """Genres API."""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    @action(detail=True, methods=["get"])
    def movies(self, request, slug=None):
        """GET /api/movies/genres/{slug}/movies/ → movies in this genre."""
        genre = self.get_object()
        page = safe_page(request.query_params.get("page", 1))
        sort = request.query_params.get("sort", "popularity.desc")

        # Try local DB first
        local_movies = Movie.objects.filter(genres=genre).order_by("-popularity")
        if local_movies.count() >= 20:
            paginator = self.paginate_queryset(local_movies)
            serializer = MovieCompactSerializer(paginator, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback to TMDB API
        tmdb_service = get_tmdb_service()
        data = tmdb_service.get_movies_by_genre(genre.tmdb_id, page=page, sort_by=sort)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response({
            "results": serializer.data,
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0),
            "page": page,
        })


## Person ViewSet

class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """People (directors, actors) API."""
    queryset = Person.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PersonDetailSerializer
        return PersonCompactSerializer

    @action(detail=True, methods=["get"])
    def enrich(self, request, pk=None):
        person = self.get_object()
        tmdb_service = get_tmdb_service()
        data = tmdb_service.get_person_details(person.tmdb_id)
        _ensure_tmdb_ok(data)

        serializer = PersonDetailSerializer(person)
        payload = serializer.data
        if data:
            payload["biography"] = data.get("biography", payload.get("biography", ""))
            payload["birthday"] = data.get("birthday") or payload.get("birthday")
            payload["place_of_birth"] = data.get("place_of_birth", payload.get("place_of_birth", ""))

        return Response(payload)


## standalone endpoints

@api_view(["GET"])
@permission_classes([AllowAny])
def search_movies(request):
    query = request.query_params.get("q", "").strip()
    page = safe_page(request.query_params.get("page", 1))

    if not query:
        return Response(
            {"error": "Query parameter 'q' is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tmdb_service = get_tmdb_service()
    data = tmdb_service.search_movies(query, page=page)
    _ensure_tmdb_ok(data)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)

    return Response({
        "results": serializer.data,
        "total_pages": data.get("total_pages", 1),
        "total_results": data.get("total_results", 0),
        "page": page,
        "query": query,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def trending_movies(request):
    window = request.query_params.get("window", "week")
    page = safe_page(request.query_params.get("page", 1))

    tmdb_service = get_tmdb_service()
    data = tmdb_service.get_trending_movies(time_window=window, page=page)
    _ensure_tmdb_ok(data)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)

    return Response({
        "results": serializer.data,
        "total_pages": data.get("total_pages", 1),
        "page": page,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def now_playing(request):
    page = safe_page(request.query_params.get("page", 1))
    tmdb_service = get_tmdb_service()
    data = tmdb_service.get_now_playing(page=page)
    _ensure_tmdb_ok(data)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)
    return Response({"results": serializer.data, "page": page})


@api_view(["GET"])
@permission_classes([AllowAny])
def top_rated(request):
    page = safe_page(request.query_params.get("page", 1))
    tmdb_service = get_tmdb_service()
    data = tmdb_service.get_top_rated_movies(page=page)
    _ensure_tmdb_ok(data)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)
    return Response({"results": serializer.data, "page": page})


@api_view(["GET"])
@permission_classes([AllowAny])
def movie_detail_tmdb(request, tmdb_id):

    sync = request.query_params.get("sync", "false").lower() == "true"
    tmdb_service = get_tmdb_service()
    sync_service = get_movie_sync_service(tmdb_service=tmdb_service)

    if sync:
        try:
            movie = sync_service.sync_movie(tmdb_id)
            serializer = MovieDetailSerializer(movie)
            return Response(serializer.data)
        except MovieNotFoundError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except TMDBAPIError as exc:
            raise APIException(detail=str(exc))

    data = tmdb_service.get_movie_details(tmdb_id)
    _ensure_tmdb_ok(data)
    if not data:
        return Response({"error": "Movie not found"}, status=404)

    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def search_people(request):
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response({"error": "Query parameter 'q' is required"}, status=400)

    tmdb_service = get_tmdb_service()
    data = tmdb_service.search_people(query)
    _ensure_tmdb_ok(data)
    return Response(data)



MOOD_MAP = {
    "cozy-night": {
        "label": "Cozy Night In",
        "description": "Warm, comforting films perfect for a relaxed evening",
        "genres": "35,10749,16",  # Comedy, Romance, Animation
        "sort_by": "vote_average.desc",
        "vote_count_gte": 200,
        "vote_average_gte": 7.0,
    },
    "adrenaline": {
        "label": "Adrenaline Rush",
        "description": "Heart-pumping action and intense thrills",
        "genres": "28,53,80",  # Action, Thriller, Crime
        "sort_by": "popularity.desc",
        "vote_count_gte": 300,
    },
    "date-night": {
        "label": "Date Night",
        "description": "Romantic and charming films to share with someone special",
        "genres": "10749,35,18",  # Romance, Comedy, Drama
        "sort_by": "vote_average.desc",
        "vote_count_gte": 150,
        "vote_average_gte": 6.5,
    },
    "mind-bender": {
        "label": "Mind Bender",
        "description": "Thought-provoking stories that twist your perception",
        "genres": "878,9648,53",  # Sci-Fi, Mystery, Thriller
        "sort_by": "vote_average.desc",
        "vote_count_gte": 200,
        "vote_average_gte": 7.0,
    },
    "feel-good": {
        "label": "Feel Good",
        "description": "Uplifting stories that leave you smiling",
        "genres": "35,10751,16",  # Comedy, Family, Animation
        "sort_by": "vote_average.desc",
        "vote_count_gte": 150,
        "vote_average_gte": 7.0,
    },
    "edge-of-seat": {
        "label": "Edge of Your Seat",
        "description": "Suspenseful films that keep you guessing",
        "genres": "53,9648,27",  # Thriller, Mystery, Horror
        "sort_by": "popularity.desc",
        "vote_count_gte": 200,
    },
    "epic-adventure": {
        "label": "Epic Adventure",
        "description": "Grand journeys and sweeping tales of heroism",
        "genres": "12,14,878",  # Adventure, Fantasy, Sci-Fi
        "sort_by": "popularity.desc",
        "vote_count_gte": 300,
    },
    "cry-it-out": {
        "label": "Cry It Out",
        "description": "Emotional dramas that hit you right in the feels",
        "genres": "18,10749,10402",  # Drama, Romance, Music
        "sort_by": "vote_average.desc",
        "vote_count_gte": 200,
        "vote_average_gte": 7.5,
    },
    "family-fun": {
        "label": "Family Fun",
        "description": "Movies the whole family can enjoy together",
        "genres": "16,10751,12",  # Animation, Family, Adventure
        "sort_by": "popularity.desc",
        "vote_count_gte": 200,
    },
    "documentary-deep-dive": {
        "label": "Documentary Deep Dive",
        "description": "Real stories that expand your worldview",
        "genres": "99",  # Documentary
        "sort_by": "vote_average.desc",
        "vote_count_gte": 100,
        "vote_average_gte": 7.0,
    },
}


@api_view(["GET"])
@permission_classes([AllowAny])
def mood_list(request):
    moods = [
        {"slug": slug, "label": m["label"], "description": m["description"]}
        for slug, m in MOOD_MAP.items()
    ]
    return Response(moods)


@api_view(["GET"])
@permission_classes([AllowAny])
def mood_movies(request, mood_slug):
    mood = MOOD_MAP.get(mood_slug)
    if not mood:
        return Response({"error": "Unknown mood"}, status=404)

    page = safe_page(request.query_params.get("page", 1))
    params = {
        "with_genres": mood["genres"],
        "sort_by": mood.get("sort_by", "popularity.desc"),
        "page": page,
    }
    if "vote_count_gte" in mood:
        params["vote_count.gte"] = mood["vote_count_gte"]
    if "vote_average_gte" in mood:
        params["vote_average.gte"] = mood["vote_average_gte"]

    tmdb_service = get_tmdb_service()
    data = tmdb_service.discover_movies(**params)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)

    return Response({
        "mood": {"slug": mood_slug, "label": mood["label"], "description": mood["description"]},
        "results": serializer.data,
        "total_pages": data.get("total_pages", 1),
        "page": page,
    })


### advanced discover / filters
@api_view(["GET"])
@permission_classes([AllowAny])
def discover_filtered(request):
    tmdb_service = get_tmdb_service()
    discovery_service = get_discovery_service(tmdb_service)
    filters = discovery_service.parse_request_filters(request.query_params)
    data = discovery_service.discover(filters)
    serializer = TMDBMovieSerializer(data.get("results", []), many=True)

    response_payload = {
        "results": serializer.data,
        "total_pages": data.get("total_pages", 1),
        "total_results": data.get("total_results", 0),
        "page": data.get("page", filters["page"]),
    }
    if data.get("query"):
        response_payload["query"] = data["query"]

    return Response(response_payload)


## movie comparison

@api_view(["GET"])
@permission_classes([AllowAny])
def compare_movies(request):
    ids_str = request.query_params.get("ids", "")
    ids = [int(i.strip()) for i in ids_str.split(",") if i.strip().isdigit()]

    if len(ids) < 2:
        return Response({"error": "Provide at least 2 TMDB IDs: ?ids=550,680"}, status=400)

    movies = []
    tmdb_service = get_tmdb_service()
    for tmdb_id in ids[:2]:
        data = tmdb_service.get_movie_details(tmdb_id)
        _ensure_tmdb_ok(data)
        if data and "id" in data:
            movies.append(data)

    if len(movies) < 2:
        return Response({"error": "Could not fetch both movies"}, status=404)

    return Response({"movies": movies})



