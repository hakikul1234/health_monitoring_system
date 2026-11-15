from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

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


class DemoSessionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # This shortcut is strictly for local development demonstrations.
        if not settings.DEBUG:
            return Response(
                {"detail": "Demo access is disabled."},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.META.get("REMOTE_ADDR") not in ("127.0.0.1", "::1"):
            return Response(
                {"detail": "Demo access is available only from this machine."},
                status=status.HTTP_403_FORBIDDEN
            )

        User = get_user_model()

        try:
            user = User.objects.get(username="astra_mission_control_demo")
        except User.DoesNotExist:
            return Response(
                {"detail": "Mission Control demo account was not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        profile = getattr(user, "astra_profile", None)

        if (
            not user.is_active
            or profile is None
            or profile.role != "MISSION_CONTROL"
        ):
            return Response(
                {"detail": "The configured demo account is not an active Mission Control account."},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK
        )


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
