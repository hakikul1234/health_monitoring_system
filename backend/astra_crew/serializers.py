from rest_framework import serializers

from astra_accounts.models import UserProfile
from .models import Astronaut


class AstronautSerializer(serializers.ModelSerializer):

    profile_id = serializers.PrimaryKeyRelatedField(
        source="profile",
        queryset=UserProfile.objects.filter(
            role=UserProfile.Role.ASTRONAUT
        ),
        write_only=True
    )

    profile = serializers.SerializerMethodField()

    class Meta:
        model = Astronaut

        fields = [
            "id",
            "profile",
            "profile_id",
            "astronaut_code",
            "call_sign",
            "designation",
            "mission_specialization",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def get_profile(self, obj):
        return {
            "user_id": obj.profile.user_id,
            "username": obj.profile.user.username,
            "full_name": obj.profile.full_name,
            "role": obj.profile.role,
            "badge_id": obj.profile.badge_id,
        }

    def validate(self, attrs):

        profile = attrs.get(
            "profile",
            getattr(self.instance, "profile", None)
        )

        if profile:
            existing = Astronaut.objects.filter(
                profile=profile
            )

            if self.instance:
                existing = existing.exclude(
                    pk=self.instance.pk
                )

            if existing.exists():
                raise serializers.ValidationError({
                    "profile_id": "This user already has an astronaut record."
                })

        return attrs
