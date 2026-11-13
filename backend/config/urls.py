from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/auth/", include("astra_accounts.urls")),

    path("api/crew/", include("astra_crew.urls")),

    path("api/missions/", include("astra_missions.urls")),

    path("api/health/", include("astra_health.urls")),

    path("api/simulator/", include("astra_simulator.urls")),
    path("api/alerts/", include("astra_alerts.urls")),
]
