from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import DashboardAnalyticsPermission
from .services.dashboard_analytics import get_dashboard_analytics


class DashboardAnalyticsView(APIView):

    permission_classes = [
        IsAuthenticated,
        DashboardAnalyticsPermission,
    ]

    def get(self, request, *args, **kwargs):

        dashboard_data = get_dashboard_analytics(request.user)

        return Response(
            dashboard_data,
            status=status.HTTP_200_OK
        )
