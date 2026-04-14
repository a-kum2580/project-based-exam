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
from .services.tmdb_service import TMDBService, MovieSyncService, WikipediaService

logger = logging.getLogger(__name__)
tmdb = TMDBService()
sync_service = MovieSyncService()


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
        data = tmdb.get_movie_recommendations(movie.tmdb_id)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        movie = self.get_object()
        data = tmdb.get_similar_movies(movie.tmdb_id)
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
        page = safe_int(request.query_params.get("page", 1))
        sort = request.query_params.get("sort", "popularity.desc")

        # Try local DB first
        local_movies = Movie.objects.filter(genres=genre).order_by("-popularity")
        if local_movies.count() >= 20:
            paginator = self.paginate_queryset(local_movies)
            serializer = MovieCompactSerializer(paginator, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback to TMDB API
        data = tmdb.get_movies_by_genre(genre.tmdb_id, page=page, sort_by=sort)
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
        data = tmdb.get_person_details(person.tmdb_id)

        if data:
            person.biography = data.get("biography", "")
            person.birthday = data.get("birthday") or None
            person.place_of_birth = data.get("place_of_birth", "")
            person.save()

        serializer = PersonDetailSerializer(person)
        return Response(serializer.data)


## standalone endpoints

@api_view(["GET"])
@permission_classes([AllowAny])
def search_movies(request):
    query = request.query_params.get("q", "").strip()
    page = safe_int(request.query_params.get("page", 1))

    if not query:
        return Response(
            {"error": "Query parameter 'q' is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = tmdb.search_movies(query, page=page)
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
    page = safe_int(request.query_params.get("page", 1))

    data = tmdb.get_trending_movies(time_window=window, page=page)
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
    page = safe_int(request.query_params.get("page", 1))
    data = tmdb.get_now_playing(page=page)
    _ensure_tmdb_ok(data)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)
    return Response({"results": serializer.data, "page": page})


@api_view(["GET"])
@permission_classes([AllowAny])
def top_rated(request):
    page = safe_int(request.query_params.get("page", 1))
    data = tmdb.get_top_rated_movies(page=page)
    _ensure_tmdb_ok(data)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)
    return Response({"results": serializer.data, "page": page})


@api_view(["GET"])
@permission_classes([AllowAny])
def movie_detail_tmdb(request, tmdb_id):

    sync = request.query_params.get("sync", "false").lower() == "true"

    if sync:
        movie = sync_service.sync_movie(tmdb_id)
        if movie:
            serializer = MovieDetailSerializer(movie)
            return Response(serializer.data)

    data = tmdb.get_movie_details(tmdb_id)
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

    data = tmdb.search_people(query)
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

    page = safe_int(request.query_params.get("page", 1))
    params = {
        "with_genres": mood["genres"],
        "sort_by": mood.get("sort_by", "popularity.desc"),
        "page": page,
    }
    if "vote_count_gte" in mood:
        params["vote_count.gte"] = mood["vote_count_gte"]
    if "vote_average_gte" in mood:
        params["vote_average.gte"] = mood["vote_average_gte"]

    data = tmdb.discover_movies(**params)
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
    page = safe_int(request.query_params.get("page", 1))
    query = request.query_params.get("q", "").strip()

    genre = request.query_params.get("genre")
    year_from = safe_int(request.query_params.get("year_from"), default=None)
    year_to = safe_int(request.query_params.get("year_to"), default=None)
    rating_min = safe_float(request.query_params.get("rating_min"), default=None)
    runtime_min = safe_int(request.query_params.get("runtime_min"), default=None)
    runtime_max = safe_int(request.query_params.get("runtime_max"), default=None)
    language = request.query_params.get("language")
    sort = request.query_params.get("sort", "popularity.desc")

    # If a search query is provided, keep filtering within that query's results.
    if query:
        first_page_data = tmdb.search_movies(query, page=1)
        _ensure_tmdb_ok(first_page_data)

        total_search_pages = safe_int(first_page_data.get("total_pages", 1), default=1)
        # TMDB search caps pagination at 500 pages; scan the full query result set.
        max_scan_pages = min(total_search_pages, 500)

        all_results = list(first_page_data.get("results", []))
        for scan_page in range(2, max_scan_pages + 1):
            page_data = tmdb.search_movies(query, page=scan_page)
            _ensure_tmdb_ok(page_data)
            all_results.extend(page_data.get("results", []))

        needs_runtime = runtime_min is not None or runtime_max is not None
        filtered = []
        for movie in all_results:
            movie_year = safe_int((movie.get("release_date") or "")[:4], default=None)
            movie_rating = safe_float(movie.get("vote_average"), default=0.0) or 0.0
            movie_genres = set(movie.get("genre_ids", []))
            movie_language = movie.get("original_language", "")

            if genre and safe_int(genre, default=None) not in movie_genres:
                continue
            if year_from and (movie_year is None or movie_year < year_from):
                continue
            if year_to and (movie_year is None or movie_year > year_to):
                continue
            if rating_min is not None and movie_rating < rating_min:
                continue
            if language and movie_language != language:
                continue

            if needs_runtime:
                detail = tmdb.get_movie_details(movie.get("id"))
                _ensure_tmdb_ok(detail)
                runtime = safe_int(detail.get("runtime"), default=None)
                if runtime_min is not None and (runtime is None or runtime < runtime_min):
                    continue
                if runtime_max is not None and (runtime is None or runtime > runtime_max):
                    continue

            filtered.append(movie)

        sort_map = {
            "popularity.desc": lambda m: safe_float(m.get("popularity"), 0.0) or 0.0,
            "vote_average.desc": lambda m: safe_float(m.get("vote_average"), 0.0) or 0.0,
            "primary_release_date.desc": lambda m: m.get("release_date") or "",
            "primary_release_date.asc": lambda m: m.get("release_date") or "",
        }
        if sort in sort_map:
            filtered.sort(key=sort_map[sort], reverse=not sort.endswith(".asc"))

        page_size = len(first_page_data.get("results", [])) or 20
        filtered_total = len(filtered)
        filtered_total_pages = max(1, (filtered_total + page_size - 1) // page_size)
        current_page = min(max(page, 1), filtered_total_pages)
        start_index = (current_page - 1) * page_size
        end_index = start_index + page_size
        page_results = filtered[start_index:end_index]

        serializer = TMDBMovieSerializer(page_results, many=True)
        return Response({
            "results": serializer.data,
            "total_pages": filtered_total_pages,
            "total_results": filtered_total,
            "page": current_page,
            "query": query,
        })

    params = {"page": page}
    if genre:
        params["with_genres"] = genre

    if year_from:
        params["primary_release_date.gte"] = f"{year_from}-01-01"
    if year_to:
        params["primary_release_date.lte"] = f"{year_to}-12-31"

    if rating_min:
        params["vote_average.gte"] = rating_min
        params["vote_count.gte"] = 50 

    if runtime_min:
        params["with_runtime.gte"] = runtime_min
    if runtime_max:
        params["with_runtime.lte"] = runtime_max

    if language:
        params["with_original_language"] = language

    params["sort_by"] = sort

    data = tmdb.discover_movies(**params)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)

    return Response({
        "results": serializer.data,
        "total_pages": data.get("total_pages", 1),
        "total_results": data.get("total_results", 0),
        "page": page,
    })


## movie comparison

@api_view(["GET"])
@permission_classes([AllowAny])
def compare_movies(request):
    ids_str = request.query_params.get("ids", "")
    ids = [int(i.strip()) for i in ids_str.split(",") if i.strip().isdigit()]

    if len(ids) < 2:
        return Response({"error": "Provide at least 2 TMDB IDs: ?ids=550,680"}, status=400)

    movies = []
    for tmdb_id in ids[:2]:
        data = tmdb.get_movie_details(tmdb_id)
        if data and "id" in data:
            movies.append(data)

    if len(movies) < 2:
        return Response({"error": "Could not fetch both movies"}, status=404)

    return Response({"movies": movies})



