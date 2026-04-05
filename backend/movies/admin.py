from django.contrib import admin
from .models import Genre, Person, Movie, MovieCast, WatchProvider


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["name", "tmdb_id", "slug"]
    search_fields = ["name"]


class MovieCastInline(admin.TabularInline):
    model = MovieCast
    extra = 0
    raw_id_fields = ["person"]


class WatchProviderInline(admin.TabularInline):
    model = WatchProvider
    extra = 0


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "release_date", "vote_average", "popularity"]
    list_filter = ["genres", "status"]
    search_fields = ["title", "original_title"]
    inlines = [MovieCastInline, WatchProviderInline]
    filter_horizontal = ["genres", "directors"]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["name", "tmdb_id", "known_for_department"]
    search_fields = ["name"]
