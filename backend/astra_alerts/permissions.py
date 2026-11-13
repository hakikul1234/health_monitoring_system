from rest_framework.permissions import BasePermission, SAFE_METHODS

from astra_accounts.models import UserProfile


class HealthAlertAccessPermission(BasePermission):

    READ_ROLES = {
        UserProfile.Role.ASTRONAUT,
        UserProfile.Role.MEDICAL_OFFICER,
        UserProfile.Role.MISSION_CONTROL,
        UserProfile.Role.SYSTEM_ADMIN,
    }

    MANAGEMENT_ROLES = {
        UserProfile.Role.MEDICAL_OFFICER,
        UserProfile.Role.MISSION_CONTROL,
        UserProfile.Role.SYSTEM_ADMIN,
    }

    def get_role(self, user):

        if not user or not user.is_authenticated:
            return None

        try:
            return user.astra_profile.role

        except UserProfile.DoesNotExist:
            return None

    def has_permission(self, request, view):

        role = self.get_role(request.user)

        if role is None:
            return False

        if request.method in SAFE_METHODS:
            return role in self.READ_ROLES

        return role in self.MANAGEMENT_ROLES

    def has_object_permission(self, request, view, obj):

        role = self.get_role(request.user)

        if role is None:
            return False

        if request.method in SAFE_METHODS:

            if role == UserProfile.Role.ASTRONAUT:
                return (
                    obj.reading.astronaut.profile.user_id
                    == request.user.id
                )

            return role in self.READ_ROLES

        return role in self.MANAGEMENT_ROLES
