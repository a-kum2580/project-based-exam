from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "avatar_url",
            "favorite_genres",
            "country_code",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]



class PasswordMatchValidator:
    """Single responsibility: validate passwords match."""

    @staticmethod
    def validate(password, password_confirm):
        if password != password_confirm:
            raise serializers.ValidationError({
                "password_confirm": "Passwords don't match."
            })



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm"]

    def validate(self, data):
        PasswordMatchValidator.validate(
            data["password"],
            data["password_confirm"]
        )
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)
