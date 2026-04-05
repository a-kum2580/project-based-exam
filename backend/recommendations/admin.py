from django.contrib import admin
from .models import UserMovieInteraction, UserGenrePreference, Watchlist

@admin.register(UserMovieInteraction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ["user", "movie_title", "interaction_type", "created_at"]
    list_filter = ["interaction_type", "created_at"]

@admin.register(UserGenrePreference)
class GenrePreferenceAdmin(admin.ModelAdmin):
    list_display = ["user", "genre_name", "weight", "interaction_count"]

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ["user", "movie_title", "watched", "added_at"]
    list_filter = ["watched"]
