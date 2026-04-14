import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Movie, Genre, Person
from .serializers import (
    MovieCompactSerializer, MovieDetailSerializer,
    GenreSerializer, PersonCompactSerializer, PersonDetailSerializer,
    TMDBMovieSerializer,
)
from .services.tmdb_service import TMDBService, MovieSyncService, WikipediaService



class ServiceContainer:
    """Centralized service access (reduces tight coupling)."""
    tmdb = TMDBService()
    sync = MovieSyncService()
    wiki = WikipediaService()


logger = logging.getLogger(__name__)



class TMDBResponseMixin:
    """Reusable logic for TMDB API serialization."""

    def tmdb_response(self, data):
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return serializer.data



class MovieViewSet(TMDBResponseMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.prefetch_related("genres", "directors").all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["genres__slug"]

    def get_serializer_class(self):
        return MovieDetailSerializer if self.action == "retrieve" else MovieCompactSerializer

    @property
    def tmdb(self):
        return ServiceContainer.tmdb

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        movie = self.get_object()
        data = self.tmdb.get_movie_recommendations(movie.tmdb_id)
        return Response(self.tmdb_response(data))

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        movie = self.get_object()
        data = self.tmdb.get_similar_movies(movie.tmdb_id)
        return Response(self.tmdb_response(data))

    @action(detail=True, methods=["get"])
    def wikipedia(self, request, pk=None):
        movie = self.get_object()
        year = movie.release_date.year if movie.release_date else None

        wiki_data = ServiceContainer.wiki.get_movie_summary(movie.title, year)

        if wiki_data.get("summary"):
            movie.wikipedia_summary = wiki_data["summary"]
            movie.wikipedia_url = wiki_data["url"]
            movie.save(update_fields=["wikipedia_summary", "wikipedia_url"])

        return Response(wiki_data)



class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    @property
    def tmdb(self):
        return ServiceContainer.tmdb

    @action(detail=True, methods=["get"])
    def movies(self, request, slug=None):
        genre = self.get_object()
        page = int(request.query_params.get("page", 1))
        sort = request.query_params.get("sort", "popularity.desc")

        local_movies = Movie.objects.filter(genres=genre).order_by("-popularity")

        if local_movies.count() >= 20:
            page_data = self.paginate_queryset(local_movies)
            serializer = MovieCompactSerializer(page_data, many=True)
            return self.get_paginated_response(serializer.data)

        data = self.tmdb.get_movies_by_genre(genre.tmdb_id, page=page, sort_by=sort)
        return Response({
            "results": self.tmdb_response(data),
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0),
            "page": page,
        })



class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        return PersonDetailSerializer if self.action == "retrieve" else PersonCompactSerializer

    @property
    def tmdb(self):
        return ServiceContainer.tmdb

    @action(detail=True, methods=["get"])
    def enrich(self, request, pk=None):
        person = self.get_object()
        data = self.tmdb.get_person_details(person.tmdb_id)

        if data:
            person.biography = data.get("biography", "")
            person.birthday = data.get("birthday") or None
            person.place_of_birth = data.get("place_of_birth", "")
            person.save()

        return Response(PersonDetailSerializer(person).data)



def _tmdb_paginated_response(data, page):
    return {
        "results": TMDBMovieSerializer(data.get("results", []), many=True).data,
        "total_pages": data.get("total_pages", 1),
        "total_results": data.get("total_results", 0),
        "page": page,
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def search_movies(request):
    query = request.query_params.get("q", "").strip()
    page = int(request.query_params.get("page", 1))

    if not query:
        return Response({"error": "Query parameter 'q' is required"}, status=400)

    data = ServiceContainer.tmdb.search_movies(query, page=page)
    return Response(_tmdb_paginated_response(data, page))


@api_view(["POST"])
@permission_classes([AllowAny])
def trending_movies(request):
    window = request.query_params.get("window", "week")
    page = int(request.query_params.get("page", 1))

    data = ServiceContainer.tmdb.get_trending_movies(time_window=window, page=page)
    return Response(_tmdb_paginated_response(data, page))


@api_view(["GET"])
@permission_classes([AllowAny])
def now_playing(request):
    page = int(request.query_params.get("page", 1))
    data = ServiceContainer.tmdb.get_now_playing(page=page)
    return Response(_tmdb_paginated_response(data, page))


@api_view(["GET"])
@permission_classes([AllowAny])
def top_rated(request):
    page = int(request.query_params.get("page", 1))
    data = ServiceContainer.tmdb.get_top_rated_movies(page=page)
    return Response(_tmdb_paginated_response(data, page))


@api_view(["GET"])
@permission_classes([AllowAny])
def movie_detail_tmdb(request, tmdb_id):
    sync = request.query_params.get("sync", "false").lower() == "true"

    if sync:
        movie = ServiceContainer.sync.sync_movie(tmdb_id)
        if movie:
            return Response(MovieDetailSerializer(movie).data)

    data = ServiceContainer.tmdb.get_movie_details(tmdb_id)
    if not data:
        return Response({"error": "Movie not found"}, status=404)

    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def search_people(request):
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response({"error": "Query parameter 'q' is required"}, status=400)

    return Response(ServiceContainer.tmdb.search_people(query))
