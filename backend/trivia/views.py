from datetime import date

from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services.daily_trivia_service import generate_daily_trivia

DAILY_TRIVIA_CACHE_TTL = 60 * 60 * 24


def build_daily_trivia_cache_key() -> str:
    return f"daily-trivia:{date.today().isoformat()}"


@api_view(["GET"])
@permission_classes([AllowAny])
def daily_trivia(request):
    cache_key = build_daily_trivia_cache_key()
    cached_payload = cache.get(cache_key)
    if cached_payload:
        return Response(cached_payload)

    payload = generate_daily_trivia()
    cache.set(cache_key, payload, DAILY_TRIVIA_CACHE_TTL)
    return Response(payload)

