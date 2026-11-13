from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .serializers import RegistrationSerializer


class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegistrationSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "Account created successfully.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.astra_profile.full_name,
                    "role": user.astra_profile.role,
                }
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(TokenObtainPairView):

    permission_classes = [AllowAny]


class RefreshTokenView(TokenRefreshView):

    permission_classes = [AllowAny]


class CurrentUserView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user
        profile = user.astra_profile

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": profile.full_name,
                "role": profile.role,
                "badge_id": profile.badge_id,
                "date_joined": user.date_joined,
            },
            status=status.HTTP_200_OK
        )
