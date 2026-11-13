from rest_framework import serializers

from astra_crew.models import Astronaut
from .models import Mission


class MissionSerializer(serializers.ModelSerializer):

    crew_ids = serializers.PrimaryKeyRelatedField(
        source="crew",
        queryset=Astronaut.objects.all(),
        many=True,
        required=False,
        write_only=True
    )

    crew = serializers.SerializerMethodField()

    created_by = serializers.SerializerMethodField()

    class Meta:

        model = Mission

        fields = [
            "id",
            "mission_code",
            "mission_name",
            "mission_type",
            "status",
            "destination",
            "description",
            "objectives",
            "planned_start_date",
            "planned_end_date",
            "crew",
            "crew_ids",
            "created_by",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def get_crew(self, obj):

        astronauts = obj.crew.select_related(
            "profile",
            "profile__user"
        )

        return [
            {
                "id": astronaut.id,
                "astronaut_code": astronaut.astronaut_code,
                "call_sign": astronaut.call_sign,
                "full_name": astronaut.profile.full_name,
                "status": astronaut.status,
            }
            for astronaut in astronauts
        ]

    def get_created_by(self, obj):

        return {
            "id": obj.created_by.id,
            "username": obj.created_by.username,
        }

    def validate(self, attrs):

        start_date = attrs.get(
            "planned_start_date",
            getattr(self.instance, "planned_start_date", None)
        )

        end_date = attrs.get(
            "planned_end_date",
            getattr(self.instance, "planned_end_date", None)
        )

        if start_date and end_date and end_date < start_date:

            raise serializers.ValidationError({
                "planned_end_date":
                    "Mission end date cannot be earlier than start date."
            })

        return attrs
