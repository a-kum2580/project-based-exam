import logging
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class TMDBErrorValidator:
    """Centralizes TMDB error detection and handling."""

    @staticmethod
    def ensure_ok(data: dict, request=None, context: str = "") -> None:
        """Check TMDB response and raise APIException if error detected."""
        if isinstance(data, dict) and data.get("_error"):
            request_id = getattr(request, "request_id", "n/a") if request else "n/a"
            logger.error(
                "TMDB failure request_id=%s context=%s error=%s",
                request_id,
                context or "unknown",
                data.get("_error"),
            )
            raise APIException(detail=data["_error"])

    @staticmethod
    def is_error(data: dict) -> bool:
        """Check if response contains error marker."""
        return isinstance(data, dict) and data.get("_error") is not None

    @staticmethod
    def get_error_message(data: dict) -> str | None:
        """Extract error message if present."""
        if isinstance(data, dict):
            return data.get("_error")
        return None
