from rest_framework.permissions import BasePermission, SAFE_METHODS

from astra_accounts.models import UserProfile


class MissionManagementPermission(BasePermission):

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

        return role in self.MANAGEMENT_ROLES

    def has_object_permission(self, request, view, obj):

        role = self.get_user_role(request.user)

        if role is None:
            return False

        if request.method in SAFE_METHODS:
            return role in self.READ_ROLES

        return role in self.MANAGEMENT_ROLES

# ==========================================================
# DASHBOARD ANALYTICS ACCESS PERMISSION
# ==========================================================

from django.core.exceptions import ObjectDoesNotExist


class DashboardAnalyticsPermission(BasePermission):

    ALLOWED_ROLES = {
        UserProfile.Role.ASTRONAUT,
        UserProfile.Role.MEDICAL_OFFICER,
        UserProfile.Role.MISSION_CONTROL,
        UserProfile.Role.SYSTEM_ADMIN,
    }

    def has_permission(self, request, view):

        user = request.user

        if not user or not user.is_authenticated:
            return False

        try:
            role = user.astra_profile.role

        except ObjectDoesNotExist:
            return False

        return role in self.ALLOWED_ROLES
