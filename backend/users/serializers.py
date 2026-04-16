from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .services.validation_policy import RegistrationValidationPolicy

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "avatar_url", "favorite_genres", "country_code", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm"]

    def _get_policy(self) -> RegistrationValidationPolicy:
        return RegistrationValidationPolicy()

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords don't match."})

        password = data.get("password") or ""
        policy = self._get_policy()
        password_error = policy.validate_password_rules(password)
        if password_error:
            raise serializers.ValidationError({"password": password_error})
        
        # Enforce strong password complexity
        validate_password(data["password"])
        
        return data

    def validate_username(self, value):
        username = value.strip()
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return username

    def validate_email(self, value):
        email = value.strip().lower()
        policy = self._get_policy()
        # Allow common email forms and any valid suffix such as .org, .edu, .io, etc.
        if not policy.is_valid_email_format(email):
            raise serializers.ValidationError(
                "Enter a valid email address with a full domain (e.g., name@domain.org)."
            )
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return email

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
