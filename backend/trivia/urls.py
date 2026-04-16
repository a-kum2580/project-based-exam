from django.urls import path

from .views import daily_trivia


urlpatterns = [
    path("daily/", daily_trivia, name="daily-trivia"),
]

