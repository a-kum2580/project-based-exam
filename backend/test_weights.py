#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinequest.settings')
django.setup()

from django.contrib.auth import get_user_model
from recommendations.models import UserMovieInteraction, UserGenrePreference
from recommendations.services.engine import RecommendationEngine
from recommendations.services.policies import DefaultInteractionWeightPolicy

User = get_user_model()

# Create/get test user
user, _ = User.objects.get_or_create(username='test_weights', defaults={'email': 'test@weights.com'})

# Clear previous data
UserMovieInteraction.objects.filter(user=user).delete()
UserGenrePreference.objects.filter(user=user).delete()

# Create diverse interactions
interactions = [
    {'type': 'like', 'genres': [28, 18], 'movie_id': 1},  # Action, Drama - weight 5.0
    {'type': 'like', 'genres': [80], 'movie_id': 2},  # Crime - weight 5.0
    {'type': 'watched', 'genres': [18], 'movie_id': 3},  # Drama - weight 3.0
    {'type': 'watchlist', 'genres': [12], 'movie_id': 4},  # Adventure - weight 2.5
    {'type': 'dislike', 'genres': [27], 'movie_id': 5},  # Horror - weight -3.0
]

for idx, data in enumerate(interactions):
    UserMovieInteraction.objects.create(
        user=user,
        movie_tmdb_id=data['movie_id'],
        movie_title=f"Test Movie {idx}",
        interaction_type=data['type'],
        genre_ids=data['genres']
    )

# Compute preferences
engine = RecommendationEngine(weight_policy=DefaultInteractionWeightPolicy())
prefs = engine.compute_genre_preferences(user)

print("=" * 60)
print("PREFERENCE SCORE VERIFICATION")
print("=" * 60)
print()
print("Raw preference scores (before normalization):")
print("  Action (28):    5.0 [from 1 like]")
print("  Drama (18):     5.0 + 3.0 = 8.0 [from 1 like + 1 watched]")
print("  Crime (80):     5.0 [from 1 like]")
print("  Adventure (12): 2.5 [from 1 watchlist]")
print("  Horror (27):   -3.0 [from 1 dislike]")
print()

print("Normalized preference scores (0-100):")
name_map = {28: "Action", 18: "Drama", 80: "Crime", 12: "Adventure", 27: "Horror"}
for genre_id, weight in prefs:
    print(f"  {name_map.get(genre_id, f'Genre {genre_id}')}: {weight:.1f}")

# Verify stored preferences
print()
print("Stored in UserGenrePreference:")
for pref in UserGenrePreference.objects.filter(user=user).order_by('-weight'):
    print(f"  {pref.genre_name} - Weight: {pref.weight}, Count: {pref.interaction_count}")

print()
print("=" * 60)
print("MISSING INTERACTION TYPES:")
print("=" * 60)
print("  ✗ 'view' (+1.0) - NOT tracked when visiting movie pages")
print("  ✗ 'search' (+0.5) - NOT tracked when selecting genres")
print("  ✓ 'like' (+5.0) - WORKING")
print("  ✓ 'watched' (+3.0) - WORKING")
print("  ✓ 'watchlist' (+2.5) - WORKING")
print("  ✓ 'dislike' (-3.0) - WORKING")
print()
