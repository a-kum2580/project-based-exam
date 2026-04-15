import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from cinequest.utils.param_parser import ParamParser
from cinequest.utils.error_validator import TMDBErrorValidator
from cinequest.utils.response_mapper import ResponseMapper

from .models import Movie, Genre, Person
from .serializers import (
    MovieCompactSerializer, MovieDetailSerializer,
    GenreSerializer, PersonCompactSerializer, PersonDetailSerializer,
    TMDBMovieSerializer,
)
from .services.discovery_service import MovieDiscoveryService
from .services.catalog_service import MovieCatalogService
from .services.tmdb_service import (
    TMDBService,
    MovieSyncService,
    WikipediaService,
    TMDBAPIError,
    MovieNotFoundError,
)
from .utils.query_params import RequestParams

logger = logging.getLogger(__name__)
PAGINATION_LIMITS = getattr(settings, "PAGINATION_LIMITS", {"max_page": 500, "compare_movies": 2})
MAX_PAGE = PAGINATION_LIMITS["max_page"]


def get_tmdb_service() -> TMDBService:
    return TMDBService()


def get_movie_sync_service(tmdb_service: TMDBService | None = None) -> MovieSyncService:
    return MovieSyncService(tmdb_client=tmdb_service)


def get_discovery_service(tmdb_service: TMDBService) -> MovieDiscoveryService:
    return MovieDiscoveryService(tmdb_client=tmdb_service, cache_ttl=300, max_scan_pages=MAX_PAGE)


def get_movie_catalog_service(tmdb_service: TMDBService | None = None) -> MovieCatalogService:
    resolved_tmdb = tmdb_service or get_tmdb_service()
    return MovieCatalogService(
        tmdb_client=resolved_tmdb,
        sync_service=get_movie_sync_service(tmdb_service=resolved_tmdb),
    )




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
        catalog_service = get_movie_catalog_service()
        data = catalog_service.get_movie_recommendations(movie.tmdb_id)
        TMDBErrorValidator.ensure_ok(data, request=request, context="movie_recommendations")
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        movie = self.get_object()
        catalog_service = get_movie_catalog_service()
        data = catalog_service.get_similar_movies(movie.tmdb_id)
        TMDBErrorValidator.ensure_ok(data, request=request, context="movie_similar")
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
        params = RequestParams(request.query_params)
        page = params.page(max_page=MAX_PAGE)
        sort = params.text("sort", "popularity.desc")

        # Try local DB first
        local_movies = Movie.objects.filter(genres=genre).order_by("-popularity")
        if local_movies.count() >= 20:
            paginator = self.paginate_queryset(local_movies)
            serializer = MovieCompactSerializer(paginator, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback to TMDB API
        catalog_service = get_movie_catalog_service()
        data = catalog_service.get_movies_by_genre(genre.tmdb_id, page=page, sort=sort)
        TMDBErrorValidator.ensure_ok(data, request=request, context="movies_by_genre")
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
        _ensure_tmdb_ok(data, request=request, context="person_enrich")

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
def search_movies(request) -> Response:
    params = RequestParams(request.query_params)
    query = params.text("q")
    page = params.page(max_page=MAX_PAGE)

    if not query:
        return ResponseMapper.bad_request("Query parameter 'q' is required")

    tmdb_service = get_tmdb_service()
    catalog_service = get_movie_catalog_service(tmdb_service=tmdb_service)
    data = catalog_service.search_movies(query, page=page)
    TMDBErrorValidator.ensure_ok(data, request=request, context="search_movies")
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
def trending_movies(request) -> Response:
    params = RequestParams(request.query_params)
    window = params.text("window", "week")
    page = params.page(max_page=MAX_PAGE)

    catalog_service = get_movie_catalog_service()
    data = catalog_service.get_trending_movies(window=window, page=page)
    TMDBErrorValidator.ensure_ok(data, request=request, context="trending_movies")
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)

    return Response({
        "results": serializer.data,
        "total_pages": data.get("total_pages", 1),
        "page": page,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def now_playing(request) -> Response:
    params = RequestParams(request.query_params)
    page = params.page(max_page=MAX_PAGE)
    catalog_service = get_movie_catalog_service()
    data = catalog_service.get_now_playing(page=page)
    TMDBErrorValidator.ensure_ok(data, request=request, context="now_playing")
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)
    return Response({"results": serializer.data, "page": page})


@api_view(["GET"])
@permission_classes([AllowAny])
def top_rated(request) -> Response:
    params = RequestParams(request.query_params)
    page = params.page(max_page=MAX_PAGE)
    catalog_service = get_movie_catalog_service()
    data = catalog_service.get_top_rated(page=page)
    TMDBErrorValidator.ensure_ok(data, request=request, context="top_rated")
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)
    return Response({"results": serializer.data, "page": page})


@api_view(["GET"])
@permission_classes([AllowAny])
def movie_detail_tmdb(request, tmdb_id) -> Response:

    sync = request.query_params.get("sync", "false").lower() == "true"
    tmdb_service = get_tmdb_service()
    catalog_service = get_movie_catalog_service(tmdb_service=tmdb_service)

    if sync:
        try:
            movie = catalog_service.sync_movie(tmdb_id)
            serializer = MovieDetailSerializer(movie, context={"request": request})
            return Response(serializer.data)
        except MovieNotFoundError as exc:
            return error_response(str(exc), status.HTTP_404_NOT_FOUND)
        except TMDBAPIError as exc:
            raise APIException(detail=str(exc))

    data = catalog_service.get_movie_details(tmdb_id)
    _ensure_tmdb_ok(data, request=request, context="movie_detail")
    if not data:
        return error_response("Movie not found", status.HTTP_404_NOT_FOUND)

    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def search_people(request) -> Response:
    params = RequestParams(request.query_params)
    query = params.text("q")
    if not query:
        return ResponseMapper.bad_request("Query parameter 'q' is required")

    catalog_service = get_movie_catalog_service()
    data = catalog_service.search_people(query)
    TMDBErrorValidator.ensure_ok(data, request=request, context="search_people")
    return Response(data)

@api_view(["GET"])
@permission_classes([AllowAny])
def mood_list(request) -> Response:
    catalog_service = get_movie_catalog_service()
    moods = catalog_service.list_moods()
    return Response(moods)


@api_view(["GET"])
@permission_classes([AllowAny])
def mood_movies(request, mood_slug: str) -> Response:
    params_parser = RequestParams(request.query_params)
    page = params_parser.page(max_page=MAX_PAGE)
    catalog_service = get_movie_catalog_service()
    mood, data = catalog_service.discover_mood_movies(mood_slug=mood_slug, page=page)
    if not mood:
        return ResponseMapper.not_found("Unknown mood")
    TMDBErrorValidator.ensure_ok(data, request=request, context="mood_movies")
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
def discover_filtered(request) -> Response:
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
def compare_movies(request) -> Response:
    ids_str = request.query_params.get("ids", "")
    ids = [int(i.strip()) for i in ids_str.split(",") if i.strip().isdigit()]

    compare_limit = PAGINATION_LIMITS["compare_movies"]
    if len(ids) < compare_limit:
        return ResponseMapper.bad_request(f"Provide at least {compare_limit} TMDB IDs: ?ids=550,680")

    catalog_service = get_movie_catalog_service()
    movies = []
    for tmdb_id in ids[:compare_limit]:
        data = catalog_service.get_movie_details(tmdb_id)
        TMDBErrorValidator.ensure_ok(data, request=request, context="compare_movies")
        if data and "id" in data:
            movies.append(data)

    if len(movies) < compare_limit:
        return ResponseMapper.not_found("Could not fetch both movies")

    return Response({"movies": movies})

