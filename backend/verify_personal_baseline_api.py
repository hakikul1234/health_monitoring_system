from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from astra_health.models import VitalSignReading

User = get_user_model()

print("\n========== AUTHENTICATED API VERIFICATION ==========")

user = User.objects.get(username="astra_mission_control_demo")

print("USER:", user.username)
print("ROLE:", user.astra_profile.role)

reading = (
    VitalSignReading.objects
    .filter(
        is_synthetic=True,
        data_quality="VALID",
    )
    .order_by("-recorded_at")
    .first()
)

if reading is None:
    raise SystemExit("No eligible synthetic reading found.")

print("READING ID:", reading.id)
print("ASTRONAUT:", reading.astronaut.astronaut_code)
print("QUALITY:", reading.data_quality)

client = APIClient()
client.force_authenticate(user=user)

response = client.get(
    f"/api/health/readings/{reading.id}/analysis/"
)

print("\nHTTP STATUS:", response.status_code)

if response.status_code != 200:
    print("API ERROR:", response.data)
    raise SystemExit("Health analysis API request failed.")

data = response.data

for key in ("analysis", "ml_analysis", "personal_baseline"):
    if key not in data:
        raise SystemExit(f"Missing response field: {key}")

print("\n========== RULE-BASED ANALYSIS ==========")
print("STATUS:", data["analysis"].get("status"))

print("\n========== ISOLATION FOREST ==========")
print("STATUS:", data["ml_analysis"].get("status"))
print("MODEL:", data["ml_analysis"].get("model"))
print("VERSION:", data["ml_analysis"].get("model_version"))

print("\n========== PERSONAL BASELINE ==========")
baseline = data["personal_baseline"]
print("STATUS:", baseline.get("status"))
print("HISTORICAL READINGS:", baseline.get("baseline_readings"))
print("MINIMUM REQUIRED:", baseline.get("minimum_required"))
print("WINDOW DAYS:", baseline.get("window_days"))
print("EXPLANATION:", baseline.get("explanation"))

print("\n========== RESPONSE VERIFICATION ==========")
print("RULE ANALYSIS: PRESENT")
print("ML ANALYSIS: PRESENT")
print("PERSONAL BASELINE: PRESENT")
print("CLINICAL VALIDATION:", baseline.get("clinical_validation"))

print("\nACTUAL API VERIFICATION PASSED")
