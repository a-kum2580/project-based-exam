from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import CustomTokenObtainPairView


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """API root — lists all available endpoints."""
    return Response({
        "message": "Welcome to the CineQuest API",
        "endpoints": {
            "admin": "/admin/",
            "auth": {
                "login (get token)": "/api/auth/token/",
                "refresh token": "/api/auth/token/refresh/",
            },
            "users": {
                "register": "/api/users/register/",
                "profile": "/api/users/profile/",
            },
            "movies": {
                "list": "/api/movies/list/",
                "genres": "/api/movies/genres/",
                "search": "/api/movies/search/?q=batman",
                "trending": "/api/movies/trending/",
                "now_playing": "/api/movies/now-playing/",
                "top_rated": "/api/movies/top-rated/",
                "moods": "/api/movies/moods/",
                "discover": "/api/movies/discover/",
                "compare": "/api/movies/compare/?ids=550,680",
            },
            "recommendations": {
                "for_you": "/api/recommendations/for-you/",
                "because_you_watched": "/api/recommendations/because-you-watched/",
                "preferences": "/api/recommendations/preferences/",
                "track": "/api/recommendations/track/",
                "watchlist": "/api/recommendations/watchlist/",
                "dashboard": "/api/recommendations/dashboard/",
            },
        },
    })


urlpatterns = [
    path("", api_root, name="api-root"),
    path("admin/", admin.site.urls),
    path("api/auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/users/", include("users.urls")),
    path("api/movies/", include("movies.urls")),
    path("api/recommendations/", include("recommendations.urls")),
]
