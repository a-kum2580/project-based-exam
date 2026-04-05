"""
Management command to sync movie data from TMDB.
Usage:
    python manage.py sync_movies --genres          # Sync all genres
    python manage.py sync_movies --trending 3      # Sync 3 pages of trending
    python manage.py sync_movies --movie 550       # Sync a specific movie (Fight Club)
"""
from django.core.management.base import BaseCommand
from movies.services.tmdb_service import MovieSyncService


class Command(BaseCommand):
    help = "Sync movie data from TMDB API"

    def add_arguments(self, parser):
        parser.add_argument("--genres", action="store_true", help="Sync all genres")
        parser.add_argument("--trending", type=int, default=0, help="Sync N pages of trending movies")
        parser.add_argument("--movie", type=int, default=0, help="Sync a specific movie by TMDB ID")

    def handle(self, *args, **options):
        service = MovieSyncService()

        if options["genres"]:
            self.stdout.write("Syncing genres...")
            service.sync_genres()
            self.stdout.write(self.style.SUCCESS("Genres synced!"))

        if options["trending"] > 0:
            pages = options["trending"]
            self.stdout.write(f"Syncing {pages} pages of trending movies...")
            service.sync_trending(pages=pages)
            self.stdout.write(self.style.SUCCESS(f"Trending movies synced ({pages} pages)!"))

        if options["movie"] > 0:
            tmdb_id = options["movie"]
            self.stdout.write(f"Syncing movie {tmdb_id}...")
            movie = service.sync_movie(tmdb_id)
            if movie:
                self.stdout.write(self.style.SUCCESS(f"Synced: {movie.title}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to sync movie {tmdb_id}"))
