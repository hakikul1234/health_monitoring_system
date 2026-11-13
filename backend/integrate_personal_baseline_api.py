from pathlib import Path

path = Path("astra_health/views.py")
source = path.read_text(encoding="utf-8")

import_anchor = "from .ai.ml_inference import run_ml_inference"

import_replacement = (
    "from .ai.ml_inference import run_ml_inference\n"
    "from .ai.personal_baseline import get_personal_baseline"
)

response_anchor = '            "ml_analysis": run_ml_inference(reading),'

response_replacement = (
    '            "ml_analysis": run_ml_inference(reading),\n'
    '            "personal_baseline": get_personal_baseline(reading),'
)

if source.count(import_anchor) != 1:
    raise SystemExit("ML import anchor not found exactly once.")

if source.count(response_anchor) != 1:
    raise SystemExit("ML response anchor not found exactly once.")

backup = path.with_name("views.py.step_14_6_7_7.backup")
backup.write_text(source, encoding="utf-8")

updated = source.replace(
    import_anchor,
    import_replacement,
    1
).replace(
    response_anchor,
    response_replacement,
    1
)

path.write_text(updated, encoding="utf-8")

print("HEALTH ANALYSIS API UPDATED")
print("BACKUP:", backup)
print("PERSONAL BASELINE IMPORT: ADDED")
print("PERSONAL BASELINE RESPONSE FIELD: ADDED")
