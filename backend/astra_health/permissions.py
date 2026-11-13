from rest_framework.permissions import BasePermission, SAFE_METHODS

from astra_accounts.models import UserProfile


class HealthReadingPermission(BasePermission):

    READ_ROLES = {
        UserProfile.Role.ASTRONAUT,
        UserProfile.Role.MEDICAL_OFFICER,
        UserProfile.Role.MISSION_CONTROL,
        UserProfile.Role.SYSTEM_ADMIN,
    }

    CREATE_ROLES = {
        UserProfile.Role.MISSION_CONTROL,
        UserProfile.Role.SYSTEM_ADMIN,
    }

    def get_user_role(self, user):

        if not user or not user.is_authenticated:
            return None

        try:
            return user.astra_profile.role
        except UserProfile.DoesNotExist:
            return None

    def has_permission(self, request, view):

        role = self.get_user_role(request.user)

        if role is None:
            return False

        if request.method in SAFE_METHODS:
            return role in self.READ_ROLES

        if request.method == "POST":
            return role in self.CREATE_ROLES

        return False

    def has_object_permission(self, request, view, obj):

        role = self.get_user_role(request.user)

        if role is None:
            return False

        if request.method in SAFE_METHODS:

            if role == UserProfile.Role.ASTRONAUT:
                return obj.astronaut.profile.user_id == request.user.id

            return role in self.READ_ROLES

        return False
