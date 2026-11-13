from rest_framework.permissions import BasePermission

from astra_accounts.models import UserProfile


class SimulatorControlPermission(BasePermission):
    """
    Only Mission Control and System Admin can
    generate synthetic telemetry through the API.
    """

    ALLOWED_ROLES = {
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

        return role in self.ALLOWED_ROLES
