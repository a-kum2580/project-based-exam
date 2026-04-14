import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.validators import RegexValidator

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "avatar_url", "favorite_genres", "country_code", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            RegexValidator(
                regex=r"^[\w\.-]+@[\w\.-]+\.\w+$",
                message="Enter a valid email address with a domain (e.g., @gmail.com)."
            )
        ]
    )
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords don't match."})
        
        # Enforce strong password complexity
        validate_password(data["password"])
        
        return data

    def validate_username(self, value):
        return value.strip()

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Case-insensitive login: map input username to stored username.
        if "username" in attrs and attrs["username"]:
            match = User.objects.filter(username__iexact=attrs["username"]).only("username").first()
            attrs["username"] = match.username if match else attrs["username"]
        return super().validate(attrs)
