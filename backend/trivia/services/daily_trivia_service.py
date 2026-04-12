import hashlib
import random
from datetime import date

from django.db.models import Count

from movies.models import Movie, Person


def _build_release_year_question(movie, rng):
    if not movie.release_date:
        return None

    correct_year = movie.release_date.year
    option_years = {correct_year}
    current_year = date.today().year

    while len(option_years) < 4:
        delta = rng.randint(1, 12)
        direction = -1 if rng.random() < 0.5 else 1
        candidate = correct_year + (delta * direction)
        if 1900 <= candidate <= current_year:
            option_years.add(candidate)

    options = [str(year) for year in option_years]
    rng.shuffle(options)

    return {
        "kind": "release_year",
        "prompt": f"In which year was '{movie.title}' released?",
        "options": options,
        "correct_index": options.index(str(correct_year)),
        "movie_tmdb_id": movie.tmdb_id,
        "movie_title": movie.title,
    }


def _build_actor_question(movie, rng, all_person_names):
    cast_names = [person.name for person in movie.cast.all() if person.name]
    unique_cast_names = list(dict.fromkeys(cast_names))
    if not unique_cast_names:
        return None

    correct_actor = rng.choice(unique_cast_names)
    distractors = [name for name in all_person_names if name and name not in unique_cast_names]
    if len(distractors) < 3:
        return None

    options = [correct_actor, *rng.sample(distractors, 3)]
    rng.shuffle(options)

    return {
        "kind": "cast_member",
        "prompt": f"Which actor appears in '{movie.title}'?",
        "options": options,
        "correct_index": options.index(correct_actor),
        "movie_tmdb_id": movie.tmdb_id,
        "movie_title": movie.title,
    }


def generate_daily_trivia():
    trivia_date = date.today().isoformat()
    seed_raw = f"cinema-trivia-{trivia_date}"
    seed = int(hashlib.sha256(seed_raw.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)

    movie_candidates = list(
        Movie.objects.filter(release_date__isnull=False)
        .annotate(cast_count=Count("cast", distinct=True))
        .filter(cast_count__gte=1)
        .prefetch_related("cast")
    )
    if not movie_candidates:
        return {"date": trivia_date, "questions": []}

    rng.shuffle(movie_candidates)
    movie_candidates = movie_candidates[:160]
    all_person_names = list(Person.objects.exclude(name="").values_list("name", flat=True)[:2000])

    questions = []
    used_movie_ids = set()
    max_attempts = max(30, len(movie_candidates) * 2)
    attempts = 0

    while len(questions) < 5 and attempts < max_attempts:
        attempts += 1
        movie = rng.choice(movie_candidates)
        if movie.id in used_movie_ids:
            continue

        if len(questions) % 2 == 0:
            question = _build_actor_question(movie, rng, all_person_names)
            if not question:
                question = _build_release_year_question(movie, rng)
        else:
            question = _build_release_year_question(movie, rng)
            if not question:
                question = _build_actor_question(movie, rng, all_person_names)

        if not question:
            continue

        used_movie_ids.add(movie.id)
        question["id"] = len(questions) + 1
        questions.append(question)

    return {"date": trivia_date, "questions": questions[:5]}

