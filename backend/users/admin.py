from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "country_code", "date_joined"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("CineQuest", {"fields": ("avatar_url", "favorite_genres", "country_code")}),
    )
