from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"genres", views.GenreViewSet, basename="genre")
router.register(r"people", views.PersonViewSet, basename="person")
router.register(r"", views.MovieViewSet, basename="movie")

urlpatterns = [
    path("search/", views.search_movies, name="search-movies"),
    path("trending/", views.trending_movies, name="trending-movies"),
    path("now-playing/", views.now_playing, name="now-playing"),
    path("top-rated/", views.top_rated, name="top-rated"),
    path("tmdb/<int:tmdb_id>/", views.movie_detail_tmdb, name="movie-detail-tmdb"),
    path("people/search/", views.search_people, name="search-people"),
    path("moods/", views.mood_list, name="mood-list"),
    path("moods/<str:mood_slug>/", views.mood_movies, name="mood-movies"),
    path("discover/", views.discover_filtered, name="discover-filtered"),
    path("compare/", views.compare_movies, name="compare-movies"),
    # Backward-compatible aliases for older frontend routes.
    path("list/", views.MovieViewSet.as_view({"get": "list"}), name="movie-list-legacy"),
    path("list/<int:pk>/", views.MovieViewSet.as_view({"get": "retrieve"}), name="movie-detail-legacy"),
    path("", include(router.urls)),
]
