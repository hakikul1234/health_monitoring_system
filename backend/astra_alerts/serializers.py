from rest_framework import serializers

from .models import HealthAlert


class HealthAlertSerializer(serializers.ModelSerializer):

    astronaut = serializers.SerializerMethodField()
    mission = serializers.SerializerMethodField()

    acknowledged_by_username = serializers.CharField(
        source="acknowledged_by.username",
        read_only=True,
        allow_null=True
    )

    resolved_by_username = serializers.CharField(
        source="resolved_by.username",
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = HealthAlert

        fields = [
            "id",
            "reading",
            "astronaut",
            "mission",
            "severity",
            "parameter",
            "rule_code",
            "observed_value",
            "explanation",
            "status",
            "acknowledged_by",
            "acknowledged_by_username",
            "acknowledged_at",
            "resolved_by",
            "resolved_by_username",
            "resolved_at",
            "resolution_notes",
            "is_synthetic",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_astronaut(self, obj):
        astronaut = obj.reading.astronaut

        return {
            "id": astronaut.id,
            "astronaut_code": astronaut.astronaut_code,
            "call_sign": astronaut.call_sign,
            "full_name": astronaut.profile.full_name,
        }

    def get_mission(self, obj):
        mission = obj.reading.mission

        if mission is None:
            return None

        return {
            "id": mission.id,
            "mission_code": mission.mission_code,
            "mission_name": mission.mission_name,
        }


class AlertResolutionSerializer(serializers.Serializer):

    resolution_notes = serializers.CharField(
        max_length=5000,
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )
