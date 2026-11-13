from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from astra_accounts.models import UserProfile

from .models import Astronaut
from .serializers import AstronautSerializer
from .permissions import AstronautManagementPermission


class AstronautListCreateView(generics.ListCreateAPIView):

    serializer_class = AstronautSerializer

    permission_classes = [
        IsAuthenticated,
        AstronautManagementPermission,
    ]

    def get_queryset(self):

        queryset = Astronaut.objects.select_related(
            "profile",
            "profile__user"
        )

        role = self.request.user.astra_profile.role

        if role == UserProfile.Role.ASTRONAUT:

            queryset = queryset.filter(
                profile__user=self.request.user
            )

        return queryset


class AstronautDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = AstronautSerializer

    permission_classes = [
        IsAuthenticated,
        AstronautManagementPermission,
    ]

    lookup_field = "pk"

    def get_queryset(self):

        queryset = Astronaut.objects.select_related(
            "profile",
            "profile__user"
        )

        role = self.request.user.astra_profile.role

        if role == UserProfile.Role.ASTRONAUT:

            queryset = queryset.filter(
                profile__user=self.request.user
            )

        return queryset
