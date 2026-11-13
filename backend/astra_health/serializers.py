from rest_framework import serializers

from astra_crew.models import Astronaut
from astra_missions.models import Mission
from .models import VitalSignReading


class VitalSignReadingSerializer(serializers.ModelSerializer):

    astronaut_id = serializers.PrimaryKeyRelatedField(
        source="astronaut",
        queryset=Astronaut.objects.select_related(
            "profile",
            "profile__user"
        ),
        write_only=True
    )

    astronaut = serializers.SerializerMethodField()

    mission_id = serializers.PrimaryKeyRelatedField(
        source="mission",
        queryset=Mission.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    mission = serializers.SerializerMethodField()

    class Meta:
        model = VitalSignReading

        fields = [
            "id",
            "sample_id",
            "astronaut",
            "astronaut_id",
            "mission",
            "mission_id",
            "heart_rate_bpm",
            "spo2_percent",
            "body_temperature_c",
            "respiratory_rate_bpm",
            "recorded_at",
            "data_quality",
            "data_source",
            "is_synthetic",
            "quality_notes",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "sample_id",
            "astronaut",
            "mission",
            "is_synthetic",
            "created_at",
        ]

    def get_astronaut(self, obj):
        return {
            "id": obj.astronaut.id,
            "astronaut_code": obj.astronaut.astronaut_code,
            "call_sign": obj.astronaut.call_sign,
            "full_name": obj.astronaut.profile.full_name,
        }

    def get_mission(self, obj):
        if not obj.mission:
            return None

        return {
            "id": obj.mission.id,
            "mission_code": obj.mission.mission_code,
            "mission_name": obj.mission.mission_name,
            "status": obj.mission.status,
        }

    def validate_heart_rate_bpm(self, value):
        if not 1 <= value <= 300:
            raise serializers.ValidationError(
                "Heart rate must be between 1 and 300 BPM."
            )
        return value

    def validate_spo2_percent(self, value):
        if not 1 <= value <= 100:
            raise serializers.ValidationError(
                "SpO2 must be between 1 and 100 percent."
            )
        return value

    def validate_body_temperature_c(self, value):
        if not 20 <= value <= 60:
            raise serializers.ValidationError(
                "Temperature must be between 20 and 60 degrees Celsius."
            )
        return value

    def validate_respiratory_rate_bpm(self, value):
        if not 1 <= value <= 100:
            raise serializers.ValidationError(
                "Respiratory rate must be between 1 and 100."
            )
        return value

    def validate(self, attrs):

        astronaut = attrs.get(
            "astronaut",
            getattr(self.instance, "astronaut", None)
        )

        mission = attrs.get(
            "mission",
            getattr(self.instance, "mission", None)
        )

        if mission and astronaut:
            if not mission.crew.filter(pk=astronaut.pk).exists():
                raise serializers.ValidationError({
                    "mission_id": (
                        "The selected astronaut is not assigned "
                        "to this mission."
                    )
                })

        return attrs
