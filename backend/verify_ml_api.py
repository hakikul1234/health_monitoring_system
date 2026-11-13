from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from astra_health.models import VitalSignReading
from astra_health.views import HealthReadingAnalysisView

User = get_user_model()

print("\n========== STEP 1: FIND MISSION CONTROL USER ==========")

user = User.objects.filter(
    astra_profile__role="MISSION_CONTROL"
).first()

assert user is not None, "Mission Control user not found."

print("MISSION CONTROL USER FOUND:", user.username)

print("\n========== STEP 2: FIND SYNTHETIC READING ==========")

reading = VitalSignReading.objects.filter(
    is_synthetic=True
).select_related(
    "astronaut",
    "astronaut__profile",
    "mission",
).order_by("-id").first()

assert reading is not None, "No synthetic reading found."

print("READING ID:", reading.id)
print("DATA QUALITY:", reading.data_quality)
print("SYNTHETIC:", reading.is_synthetic)

print("\n========== STEP 3: CALL HEALTH ANALYSIS API ==========")

factory = APIRequestFactory()

request = factory.get(
    f"/api/health/readings/{reading.id}/analysis/"
)

force_authenticate(request, user=user)

view = HealthReadingAnalysisView.as_view()

response = view(request, pk=reading.id)

print("HTTP STATUS:", response.status_code)

assert response.status_code == 200, (
    f"Unexpected API status: {response.status_code}"
)

print("\n========== STEP 4: VERIFY RESPONSE STRUCTURE ==========")

data = response.data

assert data["success"] is True
assert "analysis" in data
assert "ml_analysis" in data

ml = data["ml_analysis"]

print("RULE-BASED ANALYSIS:", data["analysis"]["status"])
print("ML STATUS:", ml["status"])
print("ML MODEL:", ml["model_type"])
print("ML VERSION:", ml["model_version"])
print("ML SCORE:", ml["anomaly_score"])
print("DATA QUALITY:", ml["data_quality"])
print("CLINICAL VALIDATION:", ml["clinical_validation"])

assert ml["model_type"] == "ISOLATION_FOREST"
assert ml["model_version"] == "v1.0.0"
assert ml["clinical_validation"] is False

print("\n========== STEP 5: VERIFY API DISCLAIMER ==========")

assert "disclaimer" in data
print(data["disclaimer"])

print("\nACTUAL DATABASE API INTEGRATION PASSED")
