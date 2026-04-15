from rest_framework.response import Response
from rest_framework import status


class ResponseMapper:
    """Centralizes HTTP response envelope construction."""

    @staticmethod
    def error(message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
        """Build a standard error response."""
        return Response(
            {"error": message},
            status=status_code,
        )

    @staticmethod
    def success(data: dict | list, status_code: int = status.HTTP_200_OK) -> Response:
        """Build a standard success response."""
        return Response(data, status=status_code)

    @staticmethod
    def created(data: dict) -> Response:
        """Build a 201 Created response."""
        return Response(data, status=status.HTTP_201_CREATED)

    @staticmethod
    def not_found(message: str = "Not found") -> Response:
        """Build a 404 Not Found response."""
        return ResponseMapper.error(message, status.HTTP_404_NOT_FOUND)

    @staticmethod
    def bad_request(message: str) -> Response:
        """Build a 400 Bad Request response."""
        return ResponseMapper.error(message, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def paginated(results: list, total_pages: int = 1, total_results: int = 0, page: int = 1) -> dict:
        """Build a standard paginated response payload."""
        return {
            "results": results,
            "total_pages": total_pages,
            "total_results": total_results,
            "page": page,
        }
