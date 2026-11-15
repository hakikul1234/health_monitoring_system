from rest_framework import serializers

from .services.health_simulator import get_available_scenarios
from .services.habitat_simulator import get_available_habitat_scenarios


class TelemetryGenerationSerializer(serializers.Serializer):

    astronaut_id = serializers.IntegerField(min_value=1)

    mission_id = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )

    scenario = serializers.ChoiceField(
        choices=[
            (scenario, scenario)
            for scenario in get_available_scenarios()
        ]
    )

    count = serializers.IntegerField(
        min_value=1,
        max_value=1000,
        default=10,
    )

    interval_seconds = serializers.IntegerField(
        min_value=1,
        max_value=3600,
        default=60,
    )

    seed = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    start_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )


class HabitatTelemetryGenerationSerializer(serializers.Serializer):

    mission_id = serializers.IntegerField(min_value=1)

    scenario = serializers.ChoiceField(
        choices=[
            (scenario, scenario)
            for scenario in get_available_habitat_scenarios()
        ],
        default="NORMAL_HABITAT",
    )

    count = serializers.IntegerField(
        min_value=1,
        max_value=1000,
        default=10,
    )

    interval_seconds = serializers.IntegerField(
        min_value=1,
        max_value=3600,
        default=60,
    )

    seed = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    start_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    sensor_id = serializers.CharField(
        max_length=64,
        required=False,
        default="SIM-HAB-01",
        allow_blank=False,
        trim_whitespace=True,
    )
from astra_health.models import (
    VirtualHealthSensor,
    SensorSimulationRun,
)

class VirtualHealthSensorRegistrationSerializer(serializers.Serializer):

    sensor_code = serializers.CharField(max_length=64)
    astronaut_id = serializers.IntegerField(min_value=1)
    mission_id = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )
    manufacturer = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    model_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True
    )
    firmware_version = serializers.CharField(
        max_length=40, required=False, allow_blank=True
    )

    def validate_sensor_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Sensor code cannot be blank.")
        if VirtualHealthSensor.objects.filter(sensor_code=value).exists():
            raise serializers.ValidationError("Sensor code already exists.")
        return value

    def validate(self, attrs):
        from astra_crew.models import Astronaut
        from astra_missions.models import Mission

        try:
            astronaut = Astronaut.objects.get(pk=attrs["astronaut_id"])
        except Astronaut.DoesNotExist:
            raise serializers.ValidationError({
                "astronaut_id": "Astronaut does not exist."
            })

        mission_id = attrs.get("mission_id")
        mission = None

        if mission_id is not None:
            try:
                mission = Mission.objects.get(pk=mission_id)
            except Mission.DoesNotExist:
                raise serializers.ValidationError({
                    "mission_id": "Mission does not exist."
                })

            if not mission.crew.filter(pk=astronaut.pk).exists():
                raise serializers.ValidationError({
                    "mission_id": "Astronaut is not assigned to this mission."
                })

        attrs["astronaut"] = astronaut
        attrs["mission"] = mission
        return attrs


class VirtualSensorSimulationSerializer(serializers.Serializer):

    scenario = serializers.ChoiceField(
        choices=[
            (item, item)
            for item in get_available_scenarios()
        ],
        default="NORMAL_MISSION",
    )

    fault_mode = serializers.ChoiceField(
        choices=SensorSimulationRun.FaultMode.choices,
        default=SensorSimulationRun.FaultMode.NORMAL,
    )

    count = serializers.IntegerField(
        min_value=1, max_value=1000, default=10
    )

    interval_seconds = serializers.IntegerField(
        min_value=1, max_value=3600, default=60
    )

    seed = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=-(2**63),
        max_value=(2**63) - 1,
    )

    noise_level_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        default=0,
    )

    packet_loss_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        default=0,
    )

    start_at = serializers.DateTimeField(
        required=False, allow_null=True
    )

    def validate(self, attrs):
        fault_mode = attrs["fault_mode"]
        noise = attrs["noise_level_percent"]
        packet_loss = attrs["packet_loss_percent"]

        if fault_mode == SensorSimulationRun.FaultMode.NOISE:
            if noise <= 0:
                raise serializers.ValidationError({
                    "noise_level_percent": (
                        "NOISE mode requires a value greater than 0."
                    )
                })
        elif noise != 0:
            raise serializers.ValidationError({
                "noise_level_percent": (
                    "Noise level is only valid for NOISE mode."
                )
            })

        if fault_mode == SensorSimulationRun.FaultMode.DROPOUT:
            if packet_loss <= 0:
                raise serializers.ValidationError({
                    "packet_loss_percent": (
                        "DROPOUT mode requires a value greater than 0."
                    )
                })
        elif packet_loss != 0:
            raise serializers.ValidationError({
                "packet_loss_percent": (
                    "Packet loss is only valid for DROPOUT mode."
                )
            })

        return attrs


class VirtualHealthSensorResponseSerializer(serializers.ModelSerializer):

    astronaut_id = serializers.IntegerField(read_only=True)
    mission_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = VirtualHealthSensor
        fields = [
            "id",
            "sensor_code",
            "astronaut_id",
            "mission_id",
            "sensor_type",
            "manufacturer",
            "model_number",
            "firmware_version",
            "status",
            "is_synthetic",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SensorSimulationRunResponseSerializer(serializers.ModelSerializer):

    sensor_code = serializers.CharField(
        source="sensor.sensor_code",
        read_only=True,
    )

    class Meta:
        model = SensorSimulationRun
        fields = [
            "id",
            "run_id",
            "sensor",
            "sensor_code",
            "fault_mode",
            "seed",
            "noise_level_percent",
            "packet_loss_percent",
            "requested_count",
            "generated_count",
            "quality_counts",
            "status",
            "started_at",
            "completed_at",
            "is_synthetic",
            "notes",
        ]
        read_only_fields = fields

class TrustDecisionEvaluationSerializer(serializers.Serializer):

    reading_id = serializers.IntegerField(min_value=1)

    cross_check_reading_id = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        if (
            attrs.get("cross_check_reading_id") is not None
            and attrs["reading_id"] == attrs["cross_check_reading_id"]
        ):
            raise serializers.ValidationError({
                "cross_check_reading_id": (
                    "The independent reading must have a different ID."
                )
            })

        return attrs
