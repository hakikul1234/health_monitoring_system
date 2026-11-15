from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from astra_health.models import VitalSignReading

from .permissions import SimulatorControlPermission
from .serializers import TrustDecisionEvaluationSerializer
from .services.trust_decision_engine import evaluate_reading_trust


class TrustDecisionEvaluationView(APIView):

    permission_classes = [
        IsAuthenticated,
        SimulatorControlPermission,
    ]

    def post(self, request):

        serializer = TrustDecisionEvaluationSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid trust decision request.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            reading = VitalSignReading.objects.select_related(
                "astronaut",
                "sensor",
                "simulation_run",
            ).get(pk=data["reading_id"])

        except VitalSignReading.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Vital sign reading not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cross_check_reading = None
        cross_check_id = data.get("cross_check_reading_id")

        if cross_check_id is not None:
            try:
                cross_check_reading = (
                    VitalSignReading.objects.select_related(
                        "astronaut",
                        "sensor",
                        "simulation_run",
                    ).get(pk=cross_check_id)
                )

            except VitalSignReading.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Cross-check reading not found.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        result = evaluate_reading_trust(
            reading=reading,
            cross_check_reading=cross_check_reading,
        )

        return Response(
            {
                "success": True,
                "reading_id": reading.id,
                "cross_check_reading_id": (
                    cross_check_reading.id
                    if cross_check_reading is not None
                    else None
                ),
                "trust_decision": result,
                "disclaimer": (
                    "SYNTHETIC SOFTWARE DEMONSTRATION ONLY. "
                    "This decision is not a medical diagnosis, "
                    "validated sensor certification, or spacecraft "
                    "safety determination."
                ),
            },
            status=status.HTTP_200_OK,
        )
