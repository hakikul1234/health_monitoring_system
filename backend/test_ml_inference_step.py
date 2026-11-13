from types import SimpleNamespace

from astra_health.ai.ml_inference import (
    run_ml_inference,
    clear_model_cache,
    _load_cached_model,
)

clear_model_cache()

# TEST 1: NORMAL SYNTHETIC

normal = SimpleNamespace(
    is_synthetic=True,
    data_quality="VALID",
    heart_rate_bpm=75,
    spo2_percent=98,
    body_temperature_c=36.7,
    respiratory_rate_bpm=15,
)

normal_result = run_ml_inference(normal)

print("\nTEST 1: NORMAL SYNTHETIC")
print(normal_result)

assert normal_result["status"] in ("NORMAL", "ANOMALY")
assert normal_result["model_version"] == "v1.0.0"
assert isinstance(normal_result["anomaly_score"], float)


# TEST 2: EMERGENCY-LIKE SYNTHETIC

emergency = SimpleNamespace(
    is_synthetic=True,
    data_quality="SUSPECT",
    heart_rate_bpm=170,
    spo2_percent=82,
    body_temperature_c=39.2,
    respiratory_rate_bpm=35,
)

emergency_result = run_ml_inference(emergency)

print("\nTEST 2: EMERGENCY-LIKE SYNTHETIC")
print(emergency_result)

assert emergency_result["status"] == "ANOMALY"
assert emergency_result["is_anomalous"] is True
assert emergency_result["data_quality"] == "SUSPECT"


# TEST 3: UNGRADABLE

ungradable = SimpleNamespace(
    is_synthetic=True,
    data_quality="UNGRADABLE",
    heart_rate_bpm=170,
    spo2_percent=82,
    body_temperature_c=39.2,
    respiratory_rate_bpm=35,
)

ungradable_result = run_ml_inference(ungradable)

print("\nTEST 3: UNGRADABLE")
print(ungradable_result)

assert ungradable_result["status"] == "INSUFFICIENT_DATA"
assert ungradable_result["anomaly_score"] is None
assert ungradable_result["is_anomalous"] is None


# TEST 4: NON-SYNTHETIC

non_synthetic = SimpleNamespace(
    is_synthetic=False,
    data_quality="VALID",
    heart_rate_bpm=170,
    spo2_percent=82,
    body_temperature_c=39.2,
    respiratory_rate_bpm=35,
)

non_synthetic_result = run_ml_inference(non_synthetic)

print("\nTEST 4: NON-SYNTHETIC")
print(non_synthetic_result)

assert non_synthetic_result["status"] == "NOT_EVALUATED"
assert non_synthetic_result["anomaly_score"] is None


# TEST 5: MODEL CACHE

run_ml_inference(normal)

cache_info = _load_cached_model.cache_info()

print("\nMODEL CACHE:", cache_info)

assert cache_info.hits >= 1

print("\nALL FIVE ML INFERENCE TESTS PASSED")
