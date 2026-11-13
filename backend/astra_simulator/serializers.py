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
