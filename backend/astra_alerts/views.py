from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from astra_accounts.models import UserProfile

from .models import HealthAlert
from .serializers import (
    HealthAlertSerializer,
    AlertResolutionSerializer,
)
from .permissions import HealthAlertAccessPermission
from .pagination import AlertPagination
from .services.alert_filters import apply_alert_filters


def get_alert_queryset():

    return HealthAlert.objects.select_related(
        "reading",
        "reading__astronaut",
        "reading__astronaut__profile",
        "reading__astronaut__profile__user",
        "reading__mission",
        "acknowledged_by",
        "resolved_by",
    )


def get_role_scoped_queryset(user):

    queryset = get_alert_queryset()

    try:
        role = user.astra_profile.role

    except UserProfile.DoesNotExist:
        return queryset.none()

    if role == UserProfile.Role.ASTRONAUT:

        queryset = queryset.filter(
            reading__astronaut__profile__user=user
        )

    return queryset


class HealthAlertListView(generics.ListAPIView):

    serializer_class = HealthAlertSerializer

    permission_classes = [
        IsAuthenticated,
        HealthAlertAccessPermission,
    ]

    pagination_class = AlertPagination

    def get_queryset(self):

        queryset = get_role_scoped_queryset(
            self.request.user
        )

        return apply_alert_filters(
            queryset,
            self.request.query_params
        )


class HealthAlertDetailView(generics.RetrieveAPIView):

    serializer_class = HealthAlertSerializer

    permission_classes = [
        IsAuthenticated,
        HealthAlertAccessPermission,
    ]

    lookup_field = "pk"

    def get_queryset(self):

        return get_role_scoped_queryset(
            self.request.user
        )


class HealthAlertStatisticsView(APIView):

    permission_classes = [
        IsAuthenticated,
        HealthAlertAccessPermission,
    ]

    def get(self, request):

        queryset = get_role_scoped_queryset(
            request.user
        )

        queryset = apply_alert_filters(
            queryset,
            request.query_params
        )

        summary = queryset.aggregate(

            total_alerts=Count("id"),

            open_alerts=Count(
                "id",
                filter=Q(status=HealthAlert.Status.OPEN)
            ),

            acknowledged_alerts=Count(
                "id",
                filter=Q(status=HealthAlert.Status.ACKNOWLEDGED)
            ),

            resolved_alerts=Count(
                "id",
                filter=Q(status=HealthAlert.Status.RESOLVED)
            ),

            warning_alerts=Count(
                "id",
                filter=Q(severity=HealthAlert.Severity.WARNING)
            ),

            critical_alerts=Count(
                "id",
                filter=Q(severity=HealthAlert.Severity.CRITICAL)
            ),
        )

        return Response(
            {
                "success": True,
                "statistics": summary,
                "disclaimer": (
                    "Synthetic software demonstration statistics. "
                    "Not a clinical assessment."
                ),
            },
            status=status.HTTP_200_OK
        )


class HealthAlertAcknowledgeView(APIView):

    permission_classes = [
        IsAuthenticated,
        HealthAlertAccessPermission,
    ]

    def post(self, request, pk):

        with transaction.atomic():

            alert = get_object_or_404(
                get_alert_queryset().select_for_update(),
                pk=pk
            )

            self.check_object_permissions(
                request,
                alert
            )

            if alert.status != HealthAlert.Status.OPEN:

                return Response(
                    {
                        "success": False,
                        "detail": (
                            "Only OPEN alerts can be acknowledged."
                        ),
                        "current_status": alert.status,
                    },
                    status=status.HTTP_409_CONFLICT
                )

            alert.status = HealthAlert.Status.ACKNOWLEDGED
            alert.acknowledged_by = request.user
            alert.acknowledged_at = timezone.now()

            alert.save(
                update_fields=[
                    "status",
                    "acknowledged_by",
                    "acknowledged_at",
                    "updated_at",
                ]
            )

        return Response(
            {
                "success": True,
                "message": "Alert acknowledged successfully.",
                "alert": HealthAlertSerializer(alert).data,
            },
            status=status.HTTP_200_OK
        )


class HealthAlertResolveView(APIView):

    permission_classes = [
        IsAuthenticated,
        HealthAlertAccessPermission,
    ]

    def post(self, request, pk):

        input_serializer = AlertResolutionSerializer(
            data=request.data
        )

        input_serializer.is_valid(
            raise_exception=True
        )

        resolution_notes = (
            input_serializer.validated_data["resolution_notes"]
        )

        with transaction.atomic():

            alert = get_object_or_404(
                get_alert_queryset().select_for_update(),
                pk=pk
            )

            self.check_object_permissions(
                request,
                alert
            )

            if alert.status != HealthAlert.Status.ACKNOWLEDGED:

                return Response(
                    {
                        "success": False,
                        "detail": (
                            "Only ACKNOWLEDGED alerts can be resolved."
                        ),
                        "current_status": alert.status,
                    },
                    status=status.HTTP_409_CONFLICT
                )

            alert.status = HealthAlert.Status.RESOLVED
            alert.resolved_by = request.user
            alert.resolved_at = timezone.now()
            alert.resolution_notes = resolution_notes

            alert.save(
                update_fields=[
                    "status",
                    "resolved_by",
                    "resolved_at",
                    "resolution_notes",
                    "updated_at",
                ]
            )

        return Response(
            {
                "success": True,
                "message": "Alert resolved successfully.",
                "alert": HealthAlertSerializer(alert).data,
            },
            status=status.HTTP_200_OK
        )
