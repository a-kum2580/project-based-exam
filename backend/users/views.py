from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import UserSerializer, RegisterSerializer



class ResponseFactory:
    """Centralized response creation (cleaner views)."""

    @staticmethod
    def success(data, status_code=status.HTTP_200_OK):
        return Response(data, status=status_code)

    @staticmethod
    def error(errors, status_code=status.HTTP_400_BAD_REQUEST):
        return Response(errors, status=status_code)



@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """POST /api/users/register/"""
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        return ResponseFactory.success(
            UserSerializer(user).data,
            status.HTTP_201_CREATED
        )

    return ResponseFactory.error(serializer.errors)



@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile(request):
    """GET/PATCH /api/users/profile/"""

    if request.method == "GET":
        return ResponseFactory.success(
            UserSerializer(request.user).data
        )

    serializer = UserSerializer(
        request.user,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return ResponseFactory.success(serializer.data)

    return ResponseFactory.error(serializer.errors)
