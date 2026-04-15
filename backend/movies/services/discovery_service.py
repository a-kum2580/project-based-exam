from typing import Any

from django.core.cache import cache
from rest_framework.exceptions import APIException


class MovieDiscoveryService:
    """Encapsulates advanced movie discovery/filtering logic."""

    def __init__(
        self,
        tmdb_client,
        cache_backend=cache,
        cache_ttl: int = 300,
        max_scan_pages: int = 500,
        result_buffer_multiplier: float = 2.0,
        max_consecutive_empty_pages: int = 3,
    ):
        self.tmdb = tmdb_client
        self.cache = cache_backend
        self.cache_ttl = cache_ttl
        self.max_scan_pages = max_scan_pages
        self.result_buffer_multiplier = result_buffer_multiplier
        self.max_consecutive_empty_pages = max_consecutive_empty_pages

    @staticmethod
    def _safe_int(value: Any, default: int | None = 1) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_float(value: Any, default: float | None = None) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _ensure_tmdb_ok(data: dict):
        if isinstance(data, dict) and data.get("_error"):
            raise APIException(detail=data["_error"])

    @staticmethod
    def _build_cache_key(payload: dict) -> str:
        import hashlib
        import json

        serialized = json.dumps(payload, sort_keys=True)
        digest = hashlib.md5(serialized.encode("utf-8")).hexdigest()
        return f"advanced-filter:{digest}"

    def parse_request_filters(self, query_params) -> dict:
        return {
            "page": self._safe_int(query_params.get("page", 1), default=1),
            "q": (query_params.get("q", "") or "").strip(),
            "genre": query_params.get("genre"),
            "year_from": self._safe_int(query_params.get("year_from"), default=None),
            "year_to": self._safe_int(query_params.get("year_to"), default=None),
            "rating_min": self._safe_float(query_params.get("rating_min"), default=None),
            "runtime_min": self._safe_int(query_params.get("runtime_min"), default=None),
            "runtime_max": self._safe_int(query_params.get("runtime_max"), default=None),
            "language": query_params.get("language"),
            "sort": query_params.get("sort", "popularity.desc"),
        }

    def discover(self, filters: dict) -> dict:
        if filters["q"]:
            return self._discover_with_query(filters)
        return self._discover_without_query(filters)

    def _discover_with_query(self, filters: dict) -> dict:
        cache_payload = {
            "q": filters["q"],
            "genre": filters["genre"],
            "year_from": filters["year_from"],
            "year_to": filters["year_to"],
            "rating_min": filters["rating_min"],
            "runtime_min": filters["runtime_min"],
            "runtime_max": filters["runtime_max"],
            "language": filters["language"],
            "sort": filters["sort"],
        }
        cache_key = self._build_cache_key(cache_payload)
        cached_filtered = self.cache.get(cache_key)

        if cached_filtered:
            filtered = cached_filtered.get("results", [])
            page_size = cached_filtered.get("page_size", 20)
        else:
            first_page_data = self.tmdb.search_movies(filters["q"], page=1)
            self._ensure_tmdb_ok(first_page_data)

            total_search_pages = self._safe_int(first_page_data.get("total_pages", 1), default=1) or 1
            max_scan_pages = min(total_search_pages, self.max_scan_pages)

            first_page_results = list(first_page_data.get("results", []))
            page_size = len(first_page_results) or 20
            target_results = self._target_result_count(
                requested_page=filters["page"],
                page_size=page_size,
            )

            filtered = self._apply_search_filters(first_page_results, filters)
            empty_pages = 0 if filtered else 1

            for scan_page in range(2, max_scan_pages + 1):
                if self._should_stop_scan(
                    current_count=len(filtered),
                    target_count=target_results,
                    empty_pages=empty_pages,
                ):
                    break

                page_data = self.tmdb.search_movies(filters["q"], page=scan_page)
                self._ensure_tmdb_ok(page_data)
                page_results = page_data.get("results", [])
                if not page_results:
                    break

                newly_filtered = self._apply_search_filters(page_results, filters)
                filtered.extend(newly_filtered)
                if newly_filtered:
                    empty_pages = 0
                else:
                    empty_pages += 1

            self._sort_movies(filtered, filters["sort"])
            self.cache.set(
                cache_key,
                {"results": filtered, "page_size": page_size},
                self.cache_ttl,
            )

        total = len(filtered)
        total_pages = max(1, (total + page_size - 1) // page_size)
        current_page = min(max(filters["page"], 1), total_pages)
        start_index = (current_page - 1) * page_size
        end_index = start_index + page_size
        page_results = filtered[start_index:end_index]

        return {
            "results": page_results,
            "total_pages": total_pages,
            "total_results": total,
            "page": current_page,
            "query": filters["q"],
        }

    def _discover_without_query(self, filters: dict) -> dict:
        params = {"page": filters["page"]}

        if filters["genre"]:
            params["with_genres"] = filters["genre"]

        if filters["year_from"]:
            params["primary_release_date.gte"] = f"{filters['year_from']}-01-01"
        if filters["year_to"]:
            params["primary_release_date.lte"] = f"{filters['year_to']}-12-31"

        if filters["rating_min"]:
            params["vote_average.gte"] = filters["rating_min"]
            params["vote_count.gte"] = 50

        if filters["runtime_min"]:
            params["with_runtime.gte"] = filters["runtime_min"]
        if filters["runtime_max"]:
            params["with_runtime.lte"] = filters["runtime_max"]

        if filters["language"]:
            params["with_original_language"] = filters["language"]

        params["sort_by"] = filters["sort"]

        data = self.tmdb.discover_movies(**params)

        return {
            "results": data.get("results", []),
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0),
            "page": filters["page"],
        }

    def _target_result_count(self, requested_page: int, page_size: int) -> int:
        base_needed = max(1, requested_page) * max(1, page_size)
        buffered = int(base_needed * self.result_buffer_multiplier)
        return max(base_needed, buffered)

    def _should_stop_scan(self, current_count: int, target_count: int, empty_pages: int) -> bool:
        if current_count >= target_count:
            return True
        if empty_pages >= self.max_consecutive_empty_pages:
            return True
        return False

    def _apply_search_filters(self, all_results: list[dict], filters: dict) -> list[dict]:
        needs_runtime = filters["runtime_min"] is not None or filters["runtime_max"] is not None
        filtered = []

        for movie in all_results:
            movie_year = self._safe_int((movie.get("release_date") or "")[:4], default=None)
            movie_rating = self._safe_float(movie.get("vote_average"), default=0.0) or 0.0
            movie_genres = set(movie.get("genre_ids", []))
            movie_language = movie.get("original_language", "")

            if filters["genre"] and self._safe_int(filters["genre"], default=None) not in movie_genres:
                continue
            if filters["year_from"] and (movie_year is None or movie_year < filters["year_from"]):
                continue
            if filters["year_to"] and (movie_year is None or movie_year > filters["year_to"]):
                continue
            if filters["rating_min"] is not None and movie_rating < filters["rating_min"]:
                continue
            if filters["language"] and movie_language != filters["language"]:
                continue

            if needs_runtime:
                runtime = self.tmdb.get_movie_runtime(movie.get("id"))
                if filters["runtime_min"] is not None and (runtime is None or runtime < filters["runtime_min"]):
                    continue
                if filters["runtime_max"] is not None and (runtime is None or runtime > filters["runtime_max"]):
                    continue

            filtered.append(movie)

        return filtered

    def _sort_movies(self, movies: list[dict], sort: str):
        sort_map = {
            "popularity.desc": lambda m: self._safe_float(m.get("popularity"), 0.0) or 0.0,
            "vote_average.desc": lambda m: self._safe_float(m.get("vote_average"), 0.0) or 0.0,
            "primary_release_date.desc": lambda m: m.get("release_date") or "",
            "primary_release_date.asc": lambda m: m.get("release_date") or "",
        }
        if sort in sort_map:
            movies.sort(key=sort_map[sort], reverse=not sort.endswith(".asc"))
