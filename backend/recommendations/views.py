from datetime import timedelta
from collections import Counter

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
from movies.serializers import TMDBMovieSerializer

MAX_PAGE = 500


def get_recommendation_engine() -> RecommendationEngine:
    return RecommendationEngine()


def _parse_page(request, default=1, max_page=MAX_PAGE):
    """Parse a positive int `page` query param."""
    try:
        page = int(request.query_params.get("page", default))
        if page <= 0:
            return default
        return min(page, max_page)
    except (TypeError, ValueError):
        return default


def _build_genre_distribution(interactions_qs, limit=10):
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
        {"name": genre_name_map.get(gid, f"Genre {gid}"), "tmdb_id": gid, "count": count}
        for gid, count in genre_counter.most_common(limit)
    ]


def _build_activity_timeline(interactions_qs, days=30):
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


def _build_preference_scores(user, engine, limit=10):
    """Compute and return top-N saved preference scores for the user."""
    engine.compute_genre_preferences(user)
    prefs = UserGenrePreference.objects.filter(user=user).order_by("-weight")[:limit]
    return [{"name": p.genre_name, "weight": round(p.weight, 1), "count": p.interaction_count} for p in prefs]


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
    result = {}
    for title, movies in data.items():
        result[title] = TMDBMovieSerializer(movies, many=True).data
    return Response(result)


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

    summary = {
        "total_interactions": interactions.count(),
        "likes": interactions.filter(interaction_type="like").count(),
        "dislikes": interactions.filter(interaction_type="dislike").count(),
        "watched": interactions.filter(interaction_type="watched").count(),
        "searches": interactions.filter(interaction_type="search").count(),
        "watchlist_total": watchlist.count(),
        "watchlist_watched": watchlist.filter(watched=True).count(),
        "average_rating": None,
    }

    avg_rating = interactions.filter(rating__isnull=False).aggregate(avg=Avg("rating"))["avg"]
    if avg_rating is not None:
        summary["average_rating"] = round(avg_rating, 1)

    return Response({
        "summary": summary,
        "genre_distribution": _build_genre_distribution(interactions),
        "preference_scores": _build_preference_scores(user, engine),
        "activity_timeline": _build_activity_timeline(interactions),
        "recent_activity": UserMovieInteractionSerializer(interactions.order_by("-created_at")[:10], many=True).data,
    })