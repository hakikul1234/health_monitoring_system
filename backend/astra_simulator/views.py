from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from astra_crew.models import Astronaut
from astra_missions.models import Mission
from .services.mission_digital_twin import get_mission_digital_twin_summary
from astra_health.models import VitalSignReading

from .permissions import SimulatorControlPermission
from .serializers import (
    TelemetryGenerationSerializer,
    HabitatTelemetryGenerationSerializer,
)

from .services.telemetry_engine import (
    get_telemetry_summary,
)

from .services.telemetry_pipeline import (
    generate_telemetry_with_alerts,
)

from .services.habitat_simulator import (
    generate_habitat_telemetry_batch,
    get_habitat_telemetry_summary,
    HABITAT_SCENARIOS,
)


class TelemetryGenerationView(APIView):

    permission_classes = [
        IsAuthenticated,
        SimulatorControlPermission,
    ]

    def post(self, request):

        serializer = TelemetryGenerationSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Invalid telemetry generation request.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:

            astronaut = Astronaut.objects.select_related(
                "profile",
                "profile__user",
            ).get(
                pk=data["astronaut_id"]
            )

        except Astronaut.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Astronaut not found.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        mission = None

        mission_id = data.get("mission_id")

        if mission_id is not None:

            try:

                mission = Mission.objects.get(
                    pk=mission_id
                )

            except Mission.DoesNotExist:

                return Response(
                    {
                        "success": False,
                        "message": "Mission not found.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:

            readings, alert_generation = (
                generate_telemetry_with_alerts(
                    astronaut=astronaut,
                    mission=mission,
                    scenario=data["scenario"],
                    count=data.get("count", 10),
                    interval_seconds=data.get(
                        "interval_seconds", 60
                    ),
                    seed=data.get("seed"),
                    start_at=data.get("start_at"),
                )
            )

        except ValueError as error:

            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        summary = get_telemetry_summary(readings)

        summary["first_recorded_at"] = (
            summary["first_recorded_at"].isoformat()
            if summary["first_recorded_at"]
            else None
        )

        summary["last_recorded_at"] = (
            summary["last_recorded_at"].isoformat()
            if summary["last_recorded_at"]
            else None
        )

        summary["data_quality_counts"] = {
            str(key): value
            for key, value in summary[
                "data_quality_counts"
            ].items()
        }

        reading_data = [
            {
                "id": reading.id,
                "sample_id": str(reading.sample_id),
                "astronaut_id": reading.astronaut_id,
                "mission_id": reading.mission_id,
                "heart_rate_bpm": reading.heart_rate_bpm,
                "spo2_percent": reading.spo2_percent,
                "body_temperature_c": float(
                    reading.body_temperature_c
                ),
                "respiratory_rate_bpm": (
                    reading.respiratory_rate_bpm
                ),
                "recorded_at": reading.recorded_at.isoformat(),
                "data_quality": reading.data_quality,
                "data_source": reading.data_source,
                "is_synthetic": reading.is_synthetic,
            }
            for reading in readings
        ]

        return Response(
            {
                "success": True,
                "message": (
                    "Synthetic telemetry generated successfully."
                ),
                "disclaimer": (
                    "SIMULATED DATA ONLY. "
                    "Not real astronaut telemetry or clinical data."
                ),
                "astronaut": {
                    "id": astronaut.id,
                    "astronaut_code": astronaut.astronaut_code,
                    "full_name": astronaut.profile.full_name,
                },
                "mission": (
                    {
                        "id": mission.id,
                        "mission_code": mission.mission_code,
                        "mission_name": mission.mission_name,
                    }
                    if mission
                    else None
                ),
                "scenario": data["scenario"],
                "summary": summary,
                "alert_generation": alert_generation,
                "readings": reading_data,
            },
            status=status.HTTP_201_CREATED,
        )


class HabitatTelemetryGenerationView(APIView):

    permission_classes = [
        IsAuthenticated,
        SimulatorControlPermission,
    ]

    def post(self, request):

        serializer = HabitatTelemetryGenerationSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Invalid habitat telemetry generation request.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:

            mission = Mission.objects.get(
                pk=data["mission_id"]
            )

        except Mission.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Mission not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:

            readings = generate_habitat_telemetry_batch(
                mission=mission,
                scenario=data["scenario"],
                count=data.get("count", 10),
                interval_seconds=data.get(
                    "interval_seconds", 60
                ),
                seed=data.get("seed"),
                start_at=data.get("start_at"),
                sensor_id=data.get(
                    "sensor_id", "SIM-HAB-01"
                ),
            )

        except ValueError as error:

            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        summary = get_habitat_telemetry_summary(readings)

        summary["first_recorded_at"] = (
            summary["first_recorded_at"].isoformat()
            if summary["first_recorded_at"]
            else None
        )

        summary["last_recorded_at"] = (
            summary["last_recorded_at"].isoformat()
            if summary["last_recorded_at"]
            else None
        )

        summary["data_quality_counts"] = {
            str(key): value
            for key, value in summary[
                "data_quality_counts"
            ].items()
        }

        for field in (
            "average_oxygen_partial_pressure_kpa",
            "average_cabin_pressure_kpa",
            "average_cabin_temperature_c",
            "average_relative_humidity_percent",
        ):
            if summary[field] is not None:
                summary[field] = float(summary[field])

        reading_data = [
            {
                "id": reading.id,
                "mission_id": reading.mission_id,
                "sensor_id": reading.sensor_id,
                "oxygen_partial_pressure_kpa": float(
                    reading.oxygen_partial_pressure_kpa
                ),
                "carbon_dioxide_ppm": (
                    reading.carbon_dioxide_ppm
                ),
                "cabin_pressure_kpa": float(
                    reading.cabin_pressure_kpa
                ),
                "cabin_temperature_c": float(
                    reading.cabin_temperature_c
                ),
                "relative_humidity_percent": float(
                    reading.relative_humidity_percent
                ),
                "scenario": reading.scenario,
                "data_quality": reading.data_quality,
                "recorded_at": reading.recorded_at.isoformat(),
                "is_synthetic": reading.is_synthetic,
                "quality_notes": reading.quality_notes,
            }
            for reading in readings
        ]

        return Response(
            {
                "success": True,
                "message": (
                    "Synthetic habitat telemetry generated successfully."
                ),
                "disclaimer": (
                    "SIMULATED DATA ONLY. These illustrative software-demo "
                    "values are not real spacecraft telemetry, validated "
                    "spacecraft operating limits, safety thresholds, "
                    "or environmental safety assessments."
                ),
                "mission": {
                    "id": mission.id,
                    "mission_code": mission.mission_code,
                    "mission_name": mission.mission_name,
                },
                "sensor_id": data.get(
                    "sensor_id", "SIM-HAB-01"
                ),
                "scenario": data["scenario"],
                "scenario_description": HABITAT_SCENARIOS[
                    data["scenario"]
                ]["description"],
                "summary": summary,
                "readings": reading_data,
            },
            status=status.HTTP_201_CREATED,
        )


class MissionDigitalTwinSummaryView(APIView):

    permission_classes = [
        IsAuthenticated,
        SimulatorControlPermission,
    ]

    def get(self, request, mission_id):

        try:
            mission = Mission.objects.get(pk=mission_id)

        except Mission.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Mission not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        summary = get_mission_digital_twin_summary(mission)

        return Response(
            {
                "success": True,
                "message": "Mission Digital Twin summary retrieved successfully.",
                **summary,
            },
            status=status.HTTP_200_OK,
        )
