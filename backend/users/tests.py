from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for the custom User model."""

    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.country_code, "US")

    def test_user_str(self):
        user = User.objects.create_user(username="anna", password="testpass123")
        self.assertEqual(str(user), "anna")

    def test_default_favorite_genres(self):
        user = User.objects.create_user(username="testuser2", password="testpass123")
        self.assertEqual(user.favorite_genres, [])


class RegisterAPITest(APITestCase):
    """Tests for user registration."""

    def test_register_success(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "Strongpass123!",
            "password_confirm": "Strongpass123!",
        }
        response = self.client.post("/api/users/register/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "newuser")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "Strongpass123!",
            "password_confirm": "differentpass",
        }
        response = self.client.post("/api/users/register/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "short",
            "password_confirm": "short",
        }
        response = self.client.post("/api/users/register/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username="Existing", password="testpass123")
        data = {
            "username": "existing",
            "email": "new@example.com",
            "password": "Strongpass123!",
            "password_confirm": "Strongpass123!",
        }
        response = self.client.post("/api/users/register/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileAPITest(APITestCase):
    """Tests for user profile endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get("/api/users/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_update_profile(self):
        response = self.client.patch(
            "/api/users/profile/",
            {"country_code": "UG"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["country_code"], "UG")

    def test_profile_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/users/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTAuthTest(APITestCase):
    """Tests for JWT token authentication."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_obtain_token(self):
        response = self.client.post(
            "/api/auth/token/",
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_wrong_password(self):
        response = self.client.post(
            "/api/auth/token/",
            {"username": "testuser", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        # First get tokens
        token_response = self.client.post(
            "/api/auth/token/",
            {"username": "testuser", "password": "testpass123"},
        )
        refresh = token_response.data["refresh"]

        # Then refresh
        response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
