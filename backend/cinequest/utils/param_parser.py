from typing import Any


class ParamParser:
    """Centralized query parameter parsing with type safety."""

    @staticmethod
    def safe_int(value: Any, default: int = 1) -> int:
        """Safely parse an integer, returning default on failure."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def safe_float(value: Any, default: float | None = None) -> float | None:
        """Safely parse a float, returning default on failure."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def safe_page(value: Any, default: int = 1, max_page: int = 500) -> int:
        """Parse page query params into a bounded positive page number."""
        page = ParamParser.safe_int(value, default=default)
        if page is None or page < 1:
            return default
        return min(page, max_page)
