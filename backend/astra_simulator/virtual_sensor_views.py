from django.db import IntegrityError, transaction

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from astra_health.models import (
    VirtualHealthSensor,
    SensorSimulationRun,
)

from .permissions import SimulatorControlPermission

from .serializers import (
    VirtualHealthSensorRegistrationSerializer,
    VirtualSensorSimulationSerializer,
    VirtualHealthSensorResponseSerializer,
    SensorSimulationRunResponseSerializer,
)

from .services.virtual_sensor_engine import (
    generate_virtual_sensor_run,
)

from .services.telemetry_pipeline import (
    process_virtual_sensor_readings,
)


class VirtualHealthSensorListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
        SimulatorControlPermission,
    ]

    def get(self, request):

        sensors = VirtualHealthSensor.objects.select_related(
            "astronaut",
            "astronaut__profile",
            "mission",
        ).all()

        astronaut_id = request.query_params.get("astronaut_id")
        mission_id = request.query_params.get("mission_id")
        sensor_status = request.query_params.get("status")

        if astronaut_id:
            sensors = sensors.filter(astronaut_id=astronaut_id)

        if mission_id:
            sensors = sensors.filter(mission_id=mission_id)

        if sensor_status:
            sensors = sensors.filter(status=sensor_status)

        data = VirtualHealthSensorResponseSerializer(
            sensors,
            many=True,
        ).data

        return Response({
            "success": True,
            "count": len(data),
            "sensors": data,
            "disclaimer": (
                "Registered sensors are virtual synthetic "
                "software representations, not physical devices."
            ),
        })

    def post(self, request):

        serializer = VirtualHealthSensorRegistrationSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid sensor registration request.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = dict(serializer.validated_data)

        # The serializer resolves these IDs into model instances.
        # Remove the raw ID keys to avoid duplicate FK arguments.
        data.pop("astronaut_id", None)
        data.pop("mission_id", None)

        try:
            with transaction.atomic():
                sensor = VirtualHealthSensor.objects.create(**data)

        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Sensor registration failed. "
                        "The sensor code may already exist."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "success": True,
                "message": "Virtual health sensor registered.",
                "sensor": VirtualHealthSensorResponseSerializer(
                    sensor
                ).data,
                "disclaimer": (
                    "Synthetic virtual sensor registration only. "
                    "No physical hardware is connected."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class VirtualSensorSimulationView(APIView):

    permission_classes = [
        IsAuthenticated,
        SimulatorControlPermission,
    ]

    def post(self, request, sensor_id):

        try:
            sensor = VirtualHealthSensor.objects.select_related(
                "astronaut",
                "astronaut__profile",
                "mission",
            ).get(pk=sensor_id)

        except VirtualHealthSensor.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Virtual sensor not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = VirtualSensorSimulationSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid sensor simulation request.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            result = generate_virtual_sensor_run(
                sensor=sensor,
                scenario=data.get("scenario", "NORMAL_MISSION"),
                fault_mode=data.get(
                    "fault_mode",
                    SensorSimulationRun.FaultMode.NORMAL,
                ),
                count=data.get("count", 10),
                interval_seconds=data.get("interval_seconds", 60),
                seed=data.get("seed"),
                noise_level_percent=data.get(
                    "noise_level_percent", 0
                ),
                packet_loss_percent=data.get(
                    "packet_loss_percent", 0
                ),
                start_at=data.get("start_at"),
            )

        except (ValueError, TypeError) as error:
            return Response(
                {
                    "success": False,
                    "message": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        run = result["run"]
        readings = result["readings"]
        fault_mode = run.fault_mode

        allow_health_alerts = fault_mode in (
            SensorSimulationRun.FaultMode.NORMAL,
            SensorSimulationRun.FaultMode.DROPOUT,
        )

        alert_generation = process_virtual_sensor_readings(
            readings,
            allow_health_alerts=allow_health_alerts,
        )

        reading_data = [
            {
                "id": reading.id,
                "sample_id": str(reading.sample_id),
                "astronaut_id": reading.astronaut_id,
                "mission_id": reading.mission_id,
                "sensor_id": reading.sensor_id,
                "simulation_run_id": reading.simulation_run_id,
                "heart_rate_bpm": reading.heart_rate_bpm,
                "spo2_percent": reading.spo2_percent,
                "body_temperature_c": float(
                    reading.body_temperature_c
                ),
                "respiratory_rate_bpm": reading.respiratory_rate_bpm,
                "recorded_at": reading.recorded_at.isoformat(),
                "data_quality": reading.data_quality,
                "data_source": reading.data_source,
                "is_synthetic": reading.is_synthetic,
                "quality_notes": reading.quality_notes,
            }
            for reading in readings
        ]

        return Response(
            {
                "success": True,
                "message": "Virtual sensor simulation completed.",
                "sensor": VirtualHealthSensorResponseSerializer(
                    sensor
                ).data,
                "run": SensorSimulationRunResponseSerializer(
                    run
                ).data,
                "summary": result["summary"],
                "alert_generation": alert_generation,
                "readings": reading_data,
                "disclaimer": (
                    "SIMULATED DATA ONLY. These values are generated "
                    "by a software demonstration engine. They are not "
                    "real astronaut measurements, validated hardware "
                    "behavior, medical diagnoses, or spacecraft safety limits."
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class SensorSimulationRunListView(APIView):

    permission_classes = [
        IsAuthenticated,
        SimulatorControlPermission,
    ]

    def get(self, request):

        runs = SensorSimulationRun.objects.select_related(
            "sensor",
            "sensor__astronaut",
            "sensor__mission",
        )

        sensor_id = request.query_params.get("sensor_id")
        fault_mode = request.query_params.get("fault_mode")
        run_status = request.query_params.get("status")

        if sensor_id:
            runs = runs.filter(sensor_id=sensor_id)

        if fault_mode:
            runs = runs.filter(fault_mode=fault_mode)

        if run_status:
            runs = runs.filter(status=run_status)

        runs = runs.order_by("-started_at")[:100]

        data = SensorSimulationRunResponseSerializer(
            runs,
            many=True,
        ).data

        return Response({
            "success": True,
            "count": len(data),
            "runs": data,
            "limit": 100,
            "disclaimer": (
                "Simulation history contains synthetic software records only."
            ),
        })
