from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from astra_accounts.models import UserProfile

from .models import Mission
from .serializers import MissionSerializer
from .permissions import MissionManagementPermission


class MissionListCreateView(generics.ListCreateAPIView):

    serializer_class = MissionSerializer

    permission_classes = [
        IsAuthenticated,
        MissionManagementPermission,
    ]

    def get_queryset(self):

        queryset = Mission.objects.select_related(
            "created_by"
        ).prefetch_related(
            "crew",
            "crew__profile",
            "crew__profile__user"
        )

        try:
            role = self.request.user.astra_profile.role

        except UserProfile.DoesNotExist:
            return queryset.none()

        if role == UserProfile.Role.ASTRONAUT:

            queryset = queryset.filter(
                crew__profile__user=self.request.user
            ).distinct()

        return queryset

    def perform_create(self, serializer):

        serializer.save(
            created_by=self.request.user
        )


class MissionDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = MissionSerializer

    permission_classes = [
        IsAuthenticated,
        MissionManagementPermission,
    ]

    lookup_field = "pk"

    def get_queryset(self):

        queryset = Mission.objects.select_related(
            "created_by"
        ).prefetch_related(
            "crew",
            "crew__profile",
            "crew__profile__user"
        )

        try:
            role = self.request.user.astra_profile.role

        except UserProfile.DoesNotExist:
            return queryset.none()

        if role == UserProfile.Role.ASTRONAUT:

            queryset = queryset.filter(
                crew__profile__user=self.request.user
            ).distinct()

        return queryset
