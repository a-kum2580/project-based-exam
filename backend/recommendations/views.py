from datetime import timedelta
from collections import Counter
from typing import Any

from django.conf import settings
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserMovieInteraction, UserGenrePreference, Watchlist
from .serializers import (
    UserMovieInteractionSerializer,
    UserGenrePreferenceSerializer,
    WatchlistSerializer,
)
from .services.engine import RecommendationEngine
from .services.policies import DefaultInteractionWeightPolicy
from movies.services.tmdb_service import TMDBService
from cinequest.utils.param_parser import ParamParser
from movies.serializers import TMDBMovieSerializer

PAGINATION_LIMITS = getattr(settings, "PAGINATION_LIMITS", {"max_page": 500, "recent_interactions": 10})
MAX_PAGE = PAGINATION_LIMITS["max_page"]

TMDB_GENRE_NAME_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western",
}


def _resolve_genre_name(genre_id: int, local_map: dict[int, str] | None = None) -> str:
    if local_map and genre_id in local_map:
        return local_map[genre_id]
    return TMDB_GENRE_NAME_MAP.get(genre_id, f"Genre {genre_id}")


def get_recommendation_engine() -> RecommendationEngine:
    return RecommendationEngine(
        tmdb_client=get_tmdb_service(),
        weight_policy=DefaultInteractionWeightPolicy(),
    )


def get_tmdb_service() -> TMDBService:
    return TMDBService()


def _parse_page(request, default=1, max_page=MAX_PAGE) -> int:
    """Parse a positive int `page` query param."""
    return ParamParser.safe_page(request.query_params.get("page", default), default=default, max_page=max_page)


def _build_genre_distribution(interactions_qs, limit=10) -> list[dict[str, Any]]:
    """
    Build a top-N genre distribution based on stored interaction.genre_ids.
    Returns: [{name, tmdb_id, count}, ...]
    """
    from movies.models import Genre

    genre_counter = Counter()
    for interaction in interactions_qs.filter(interaction_type__in=["like", "watched", "watchlist"]):
        for gid in interaction.genre_ids:
            genre_counter[gid] += 1

    genre_name_map = {g.tmdb_id: g.name for g in Genre.objects.all()}
    return [
        {"name": _resolve_genre_name(gid, genre_name_map), "tmdb_id": gid, "count": count}
        for gid, count in genre_counter.most_common(limit)
    ]


def _build_activity_timeline(interactions_qs, days=30) -> list[dict[str, Any]]:
    """Build daily interaction counts for the last N days."""
    start = timezone.now() - timedelta(days=days)
    daily = (
        interactions_qs.filter(created_at__gte=start)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )
    return [{"date": str(d["date"]), "count": d["count"]} for d in daily]


def _build_preference_scores(user, engine, limit=10) -> list[dict[str, Any]]:
    """Compute and return top-N saved preference scores for the user."""
    from movies.models import Genre

    engine.compute_genre_preferences(user)
    prefs = UserGenrePreference.objects.filter(user=user).order_by("-weight")[:limit]
    genre_name_map = {g.tmdb_id: g.name for g in Genre.objects.all()}
    return [
        {
            "name": _resolve_genre_name(p.genre_tmdb_id, genre_name_map),
            "weight": round(p.weight, 1),
            "count": p.interaction_count,
        }
        for p in prefs
    ]


def _serialize_movie_map(movie_map: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    serialized = {}
    for title, movies in movie_map.items():
        serialized[title] = TMDBMovieSerializer(movies, many=True).data
    return serialized


def _build_dashboard_summary(interactions, watchlist) -> dict[str, Any]:
    likes_count = interactions.filter(interaction_type="like").count()
    dislikes_count = interactions.filter(interaction_type="dislike").count()
    explicit_watched_count = interactions.filter(interaction_type="watched").count()

    summary = {
        "total_interactions": interactions.count(),
        "likes": likes_count,
        "dislikes": dislikes_count,
        "watched": likes_count + dislikes_count + explicit_watched_count,
        "searches": interactions.filter(interaction_type="search").count(),
        "watchlist_total": watchlist.count(),
        "watchlist_watched": watchlist.filter(watched=True).count(),
        "average_rating": None,
    }

    avg_rating = interactions.filter(rating__isnull=False).aggregate(avg=Avg("rating"))["avg"]
    if avg_rating is not None:
        summary["average_rating"] = round(avg_rating, 1)
    return summary


def _build_recent_activity(interactions):
    return UserMovieInteractionSerializer(
        interactions.order_by("-created_at")[:PAGINATION_LIMITS["recent_interactions"]],
        many=True,
    ).data


def _build_liked_movies(interactions_qs, limit=30) -> list[dict[str, Any]]:
    """Return latest unique liked movies for dashboard display."""
    liked_rows = interactions_qs.filter(interaction_type="like").order_by("-created_at")
    seen_tmdb_ids = set()
    liked_movies = []

    for row in liked_rows:
        if row.movie_tmdb_id in seen_tmdb_ids:
            continue
        seen_tmdb_ids.add(row.movie_tmdb_id)
        liked_movies.append({
            "movie_tmdb_id": row.movie_tmdb_id,
            "movie_title": row.movie_title,
            "liked_at": row.created_at,
        })
        if len(liked_movies) >= limit:
            break

    return liked_movies


def _build_disliked_movies(interactions_qs, limit=30) -> list[dict[str, Any]]:
    """Return latest unique disliked movies for dashboard display."""
    disliked_rows = interactions_qs.filter(interaction_type="dislike").order_by("-created_at")
    seen_tmdb_ids = set()
    disliked_movies = []

    for row in disliked_rows:
        if row.movie_tmdb_id in seen_tmdb_ids:
            continue
        seen_tmdb_ids.add(row.movie_tmdb_id)
        disliked_movies.append({
            "movie_tmdb_id": row.movie_tmdb_id,
            "movie_title": row.movie_title,
            "disliked_at": row.created_at,
        })
        if len(disliked_movies) >= limit:
            break

    return disliked_movies


def _build_watched_movies(interactions_qs, limit=30) -> list[dict[str, Any]]:
    """Return recent watched events (like/dislike/watched) for dashboard display."""
    watched_rows = interactions_qs.filter(
        interaction_type__in=["like", "dislike", "watched"]
    ).order_by("-created_at")[:limit]

    return [
        {
            "movie_tmdb_id": row.movie_tmdb_id,
            "movie_title": row.movie_title,
            "watched_at": row.created_at,
            "source_interaction": row.interaction_type,
        }
        for row in watched_rows
    ]


def _build_watchlist_movies(watchlist_qs, limit=30) -> list[dict[str, Any]]:
    """Return latest watchlist entries for dashboard display."""
    rows = watchlist_qs.order_by("-added_at")[:limit]
    return [
        {
            "movie_tmdb_id": row.movie_tmdb_id,
            "movie_title": row.movie_title,
            "added_at": row.added_at,
            "watched": row.watched,
        }
        for row in rows
    ]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def personalized_recommendations(request):
    """GET /api/recommendations/for-you/ → personalized picks."""
    engine = get_recommendation_engine()
    page = _parse_page(request, default=1)
    movies = engine.get_recommendations(request.user, page=page)
    serializer = TMDBMovieSerializer(movies, many=True)
    return Response({"results": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def because_you_watched(request):
    """GET /api/recommendations/because-you-watched/"""
    engine = get_recommendation_engine()
    data = engine.get_because_you_watched(request.user)
    return Response(_serialize_movie_map(data))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def genre_preferences(request):
    """GET /api/recommendations/preferences/"""
    # Recomputing preferences
    engine = get_recommendation_engine()
    engine.compute_genre_preferences(request.user)
    prefs = UserGenrePreference.objects.filter(user=request.user)
    serializer = UserGenrePreferenceSerializer(prefs, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def track_interaction(request):
    """
    POST /api/recommendations/track/
    Body: { movie_tmdb_id, movie_title, interaction_type, genre_ids?, rating? }
    """
    serializer = UserMovieInteractionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def untrack_interaction(request):
    """
    POST /api/recommendations/untrack/
    Body: { movie_tmdb_id, interaction_type }
    Deletes matching interactions for the current user.
    """
    movie_tmdb_id = request.data.get("movie_tmdb_id")
    interaction_type = request.data.get("interaction_type")

    if movie_tmdb_id is None or not interaction_type:
        return Response(
            {"detail": "movie_tmdb_id and interaction_type are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        movie_tmdb_id = int(movie_tmdb_id)
    except (TypeError, ValueError):
        return Response({"detail": "movie_tmdb_id must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

    deleted_count, _ = UserMovieInteraction.objects.filter(
        user=request.user,
        movie_tmdb_id=movie_tmdb_id,
        interaction_type=interaction_type,
    ).delete()

    return Response({"deleted": deleted_count}, status=status.HTTP_200_OK)


class WatchlistViewSet(viewsets.ModelViewSet):
    """User's watchlist CRUD."""
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        from django.db import IntegrityError
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "This movie is already in your watchlist."})

    @action(detail=True, methods=["post"])
    def mark_watched(self, request, pk=None):
        """POST /api/recommendations/watchlist/{id}/mark_watched/"""
        item = self.get_object()
        item.watched = True
        item.watched_at = timezone.now()
        item.save()
        return Response(WatchlistSerializer(item).data)


### dashboard stats

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /api/recommendations/dashboard/
    Returns aggregated stats for the user's dashboard.
    """
    user = request.user
    engine = get_recommendation_engine()

    interactions = UserMovieInteraction.objects.filter(user=user)
    watchlist = Watchlist.objects.filter(user=user)

    summary = _build_dashboard_summary(interactions, watchlist)

    return Response({
        "summary": summary,
        "genre_distribution": _build_genre_distribution(interactions),
        "preference_scores": _build_preference_scores(user, engine),
        "activity_timeline": _build_activity_timeline(interactions),
        "recent_activity": _build_recent_activity(interactions),
        "liked_movies": _build_liked_movies(interactions),
        "disliked_movies": _build_disliked_movies(interactions),
        "watched_movies": _build_watched_movies(interactions),
        "watchlist_movies": _build_watchlist_movies(watchlist),
    })