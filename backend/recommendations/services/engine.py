import logging
from collections import Counter
from typing import Any
from django.conf import settings
from django.db.models import Avg, Count
from rest_framework.exceptions import APIException
from movies.services.tmdb_service import TMDBService
from .contracts import RecommendationTMDBClient
from .policies import DefaultInteractionWeightPolicy, InteractionWeightPolicy

logger = logging.getLogger(__name__)

PAGINATION_LIMITS = getattr(
    settings,
    "PAGINATION_LIMITS",
    {
        "top_genres": 3,
        "director_recommendations": 10,
        "because_you_watched_source": 5,
        "because_you_watched_per_movie": 5,
    },
)


class RecommendationEngine:
    """Class to generate personalized movie recommendations."""

    def __init__(
        self,
        tmdb_client: RecommendationTMDBClient | None = None,
        weight_policy: InteractionWeightPolicy | None = None,
    ):
        self.tmdb = tmdb_client or TMDBService()
        self.weight_policy = weight_policy or DefaultInteractionWeightPolicy()

    @staticmethod
    def _ensure_tmdb_ok(data: dict, context: str):
        if isinstance(data, dict) and data.get("_error"):
            logger.error("TMDB failure context=%s error=%s", context, data.get("_error"))
            raise APIException(detail=data["_error"])

    def compute_genre_preferences(self, user) -> list[tuple[int, float]]:
        from recommendations.models import UserMovieInteraction, UserGenrePreference
        from movies.models import Genre

        interactions = UserMovieInteraction.objects.filter(user=user)
        genre_scores = Counter()
        genre_interaction_counts = Counter()

        # Pre-fetch all genre names in one query to avoid N+1
        genre_names = {g.tmdb_id: g.name for g in Genre.objects.all()}

        for interaction in interactions:
            w = self.weight_policy.weight_for(interaction.interaction_type)
            for genre_id in interaction.genre_ids:
                genre_scores[genre_id] += w
                genre_interaction_counts[genre_id] += 1
                if genre_id not in genre_names:
                    genre_names[genre_id] = f"Genre {genre_id}"

        ### normalizing scores to 0-100 range
        if genre_scores:
            max_score = max(genre_scores.values())
            if max_score > 0:
                for gid in genre_scores:
                    genre_scores[gid] = (genre_scores[gid] / max_score) * 100

        ## saving preferences
        for genre_id, score in genre_scores.items():
            UserGenrePreference.objects.update_or_create(
                user=user,
                genre_tmdb_id=genre_id,
                defaults={
                    "genre_name": genre_names.get(genre_id, ""),
                    "weight": max(score, 0),
                    "interaction_count": genre_interaction_counts[genre_id],
                },
            )

        return sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)

    def get_recommendations(self, user, page: int = 1, limit: int = 20) -> list[dict[str, Any]]:
        from recommendations.models import UserMovieInteraction

        ## computing fresh preferences
        preferences = self.compute_genre_preferences(user)

        if not preferences:
            data = self.tmdb.get_trending_movies(page=page)
            self._ensure_tmdb_ok(data, context="recommendations_trending_fallback")
            return data.get("results", [])

        ## getting movies the user has already seen
        seen_ids = set(
            UserMovieInteraction.objects.filter(
                user=user,
                interaction_type__in=["watched", "dislike"],
            ).values_list("movie_tmdb_id", flat=True)
        )

        # getting top 3 genres
        top_genres = preferences[:PAGINATION_LIMITS["top_genres"]]
        if not top_genres:
            data = self.tmdb.get_trending_movies(page=page)
            self._ensure_tmdb_ok(data, context="recommendations_empty_top_genres")
            return data.get("results", [])
        all_movies = []

        for genre_id, score in top_genres:
            data = self.tmdb.discover_movies(
                with_genres=genre_id,
                sort_by="vote_average.desc",
                **{"vote_count.gte": 100},
                page=page,
            )
            self._ensure_tmdb_ok(data, context=f"recommendations_genre_{genre_id}")
            movies = data.get("results", [])
            for m in movies:
                m["_recommendation_score"] = score * m.get("vote_average", 0)
            all_movies.extend(movies)

        seen_in_batch = set()
        unique_movies = []
        for m in all_movies:
            mid = m["id"]
            if mid not in seen_ids and mid not in seen_in_batch:
                seen_in_batch.add(mid)
                unique_movies.append(m)

        ### sorting by recommendation score
        unique_movies.sort(key=lambda x: x.get("_recommendation_score", 0), reverse=True)

        # Strip internal score before returning
        for m in unique_movies:
            m.pop("_recommendation_score", None)

        return unique_movies[:limit]

    def get_director_recommendations(self, director_tmdb_id: int, exclude_movie_id: int = None) -> list[dict[str, Any]]:
        """getting other movies by a specific director."""
        data = self.tmdb.get_person_details(director_tmdb_id)
        if not data:
            return []

        credits = data.get("movie_credits", {}).get("crew", [])
        directed = [
            c for c in credits
            if c.get("job") == "Director" and c.get("id") != exclude_movie_id
        ]

        ##sorting by popularity
        directed.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        return directed[:PAGINATION_LIMITS["director_recommendations"]]

    def get_because_you_watched(self, user, limit: int = 20) -> dict[str, list[dict[str, Any]]]:
        from recommendations.models import UserMovieInteraction

        recent = UserMovieInteraction.objects.filter(
            user=user,
            interaction_type__in=["watched", "like"],
        ).order_by("-created_at")[:PAGINATION_LIMITS["because_you_watched_source"]]

        results = {}
        for interaction in recent:
            data = self.tmdb.get_movie_recommendations(interaction.movie_tmdb_id)
            self._ensure_tmdb_ok(data, context=f"because_you_watched_{interaction.movie_tmdb_id}")
            movies = data.get("results", [])[:PAGINATION_LIMITS["because_you_watched_per_movie"]]
            if movies:
                results[interaction.movie_title] = movies

        return results