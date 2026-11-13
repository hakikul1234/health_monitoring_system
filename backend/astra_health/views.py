from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from astra_accounts.models import UserProfile
from .models import VitalSignReading
from .serializers import VitalSignReadingSerializer
from .permissions import HealthReadingPermission
from .ai.anomaly_detector import detect_reading_anomalies
from .ai.ml_inference import run_ml_inference
from .ai.personal_baseline import get_personal_baseline
from .ai.predictive_analytics import get_predictive_analytics


class HealthReadingListCreateView(generics.ListCreateAPIView):

    serializer_class = VitalSignReadingSerializer

    permission_classes = [
        IsAuthenticated,
        HealthReadingPermission,
    ]

    def get_queryset(self):

        queryset = VitalSignReading.objects.select_related(
            "astronaut",
            "astronaut__profile",
            "astronaut__profile__user",
            "mission",
        )

        try:
            role = self.request.user.astra_profile.role
        except UserProfile.DoesNotExist:
            return queryset.none()

        if role == UserProfile.Role.ASTRONAUT:
            queryset = queryset.filter(
                astronaut__profile__user=self.request.user
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save()


class HealthReadingDetailView(generics.RetrieveAPIView):

    serializer_class = VitalSignReadingSerializer

    permission_classes = [
        IsAuthenticated,
        HealthReadingPermission,
    ]

    lookup_field = "pk"

    def get_queryset(self):

        queryset = VitalSignReading.objects.select_related(
            "astronaut",
            "astronaut__profile",
            "astronaut__profile__user",
            "mission",
        )

        try:
            role = self.request.user.astra_profile.role
        except UserProfile.DoesNotExist:
            return queryset.none()

        if role == UserProfile.Role.ASTRONAUT:
            queryset = queryset.filter(
                astronaut__profile__user=self.request.user
            )

        return queryset


class HealthReadingAnalysisView(APIView):

    permission_classes = [
        IsAuthenticated,
        HealthReadingPermission,
    ]

    def get(self, request, pk):

        queryset = VitalSignReading.objects.select_related(
            "astronaut",
            "astronaut__profile",
            "astronaut__profile__user",
            "mission",
        )

        try:
            role = request.user.astra_profile.role
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "User profile not found."},
                status=status.HTTP_403_FORBIDDEN
            )

        if role == UserProfile.Role.ASTRONAUT:
            queryset = queryset.filter(
                astronaut__profile__user=request.user
            )

        reading = get_object_or_404(
            queryset,
            pk=pk
        )

        self.check_object_permissions(request, reading)

        analysis = detect_reading_anomalies(reading)

        response_data = {
            "success": True,

            "reading": {
                "id": reading.id,
                "sample_id": str(reading.sample_id),
                "astronaut_code": reading.astronaut.astronaut_code,
                "mission_code": (
                    reading.mission.mission_code
                    if reading.mission
                    else None
                ),
                "recorded_at": reading.recorded_at.isoformat(),
                "data_quality": reading.data_quality,
                "is_synthetic": reading.is_synthetic,
            },

            "analysis": analysis,

            "ml_analysis": run_ml_inference(reading),
            "personal_baseline": get_personal_baseline(reading),
            "predictive_analytics": get_predictive_analytics(reading),

            "disclaimer": (
                "Synthetic software demonstration only. "
                "Not a medical diagnosis or treatment recommendation. "
                "Human review is required."
            ),
        }

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )
