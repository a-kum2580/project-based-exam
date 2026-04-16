from django.conf import settings


def build_tmdb_image_url(path: str | None, size: str) -> str | None:
    if not path:
        return None
    return f"{settings.TMDB_IMAGE_BASE_URL}/{size}{path}"


def build_youtube_watch_url(video_key: str | None) -> str | None:
    if not video_key:
        return None
    return f"https://www.youtube.com/watch?v={video_key}"


def build_youtube_embed_url(video_key: str | None) -> str | None:
    if not video_key:
        return None
    return f"https://www.youtube.com/embed/{video_key}"
