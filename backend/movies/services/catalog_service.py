from typing import Optional

from movies.config.moods import MOOD_MAP
from movies.services.tmdb_service import MovieSyncService, TMDBService


class MovieCatalogService:
    """Application service for read-only movie catalog operations."""

    def __init__(self, tmdb_client: Optional[TMDBService] = None, sync_service: Optional[MovieSyncService] = None):
        self.tmdb = tmdb_client or TMDBService()
        self.sync_service = sync_service or MovieSyncService(tmdb_client=self.tmdb)

    def get_movie_recommendations(self, movie_tmdb_id: int) -> dict:
        return self.tmdb.get_movie_recommendations(movie_tmdb_id)

    def get_similar_movies(self, movie_tmdb_id: int) -> dict:
        return self.tmdb.get_similar_movies(movie_tmdb_id)

    def get_movies_by_genre(self, genre_tmdb_id: int, page: int, sort: str) -> dict:
        return self.tmdb.get_movies_by_genre(genre_tmdb_id, page=page, sort_by=sort)

    def search_movies(self, query: str, page: int) -> dict:
        return self.tmdb.search_movies(query, page=page)

    def get_trending_movies(self, window: str, page: int) -> dict:
        return self.tmdb.get_trending_movies(time_window=window, page=page)

    def get_now_playing(self, page: int) -> dict:
        return self.tmdb.get_now_playing(page=page)

    def get_top_rated(self, page: int) -> dict:
        return self.tmdb.get_top_rated_movies(page=page)

    def sync_movie(self, tmdb_id: int):
        return self.sync_service.sync_movie(tmdb_id)

    def get_movie_details(self, tmdb_id: int) -> dict:
        return self.tmdb.get_movie_details(tmdb_id)

    def search_people(self, query: str) -> dict:
        return self.tmdb.search_people(query)

    def list_moods(self) -> list[dict[str, str]]:
        return [
            {"slug": slug, "label": mood["label"], "description": mood["description"]}
            for slug, mood in MOOD_MAP.items()
        ]

    def discover_mood_movies(self, mood_slug: str, page: int) -> tuple[Optional[dict], Optional[dict]]:
        mood = MOOD_MAP.get(mood_slug)
        if not mood:
            return None, None

        params = {
            "with_genres": mood["genres"],
            "sort_by": mood.get("sort_by", "popularity.desc"),
            "page": page,
        }
        if "vote_count_gte" in mood:
            params["vote_count.gte"] = mood["vote_count_gte"]
        if "vote_average_gte" in mood:
            params["vote_average.gte"] = mood["vote_average_gte"]

        data = self.tmdb.discover_movies(**params)
        return mood, data

