from rest_framework.permissions import BasePermission, SAFE_METHODS

from astra_accounts.models import UserProfile


class AstronautManagementPermission(BasePermission):

    READ_ROLES = {
        UserProfile.Role.ASTRONAUT,
        UserProfile.Role.MEDICAL_OFFICER,
        UserProfile.Role.MISSION_CONTROL,
        UserProfile.Role.SYSTEM_ADMIN,
    }

    MANAGEMENT_ROLES = {
        UserProfile.Role.MISSION_CONTROL,
        UserProfile.Role.SYSTEM_ADMIN,
    }

    def has_permission(self, request, view):

        if not request.user or not request.user.is_authenticated:
            return False

        try:
            role = request.user.astra_profile.role
        except UserProfile.DoesNotExist:
            return False

        if request.method in SAFE_METHODS:
            return role in self.READ_ROLES

        return role in self.MANAGEMENT_ROLES

    def has_object_permission(self, request, view, obj):

        role = request.user.astra_profile.role

        if request.method in SAFE_METHODS:

            if role == UserProfile.Role.ASTRONAUT:
                return obj.profile.user_id == request.user.id

            return role in self.READ_ROLES

        return role in self.MANAGEMENT_ROLES
