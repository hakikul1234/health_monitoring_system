from pathlib import Path

path = Path("astra_health/test_personal_baseline.py")
source = path.read_text(encoding="utf-8")

old = '''    def make_history(self, count=12, **overrides):
        return [
            self.make_reading(
                recorded_at=self.now - timedelta(minutes=10 * i + 1),
                **overrides
            )
            for i in range(count)
        ]
'''

new = '''    def make_history(self, count=12, **overrides):
        history = []

        for i in range(count):
            variation = (i % 3) - 1

            values = {
                "heart_rate_bpm": 75 + variation,
                "spo2_percent": 98 + variation,
                "body_temperature_c": 36.7 + (variation * 0.1),
                "respiratory_rate_bpm": 15 + variation,
            }

            values.update(overrides)

            history.append(
                self.make_reading(
                    recorded_at=self.now - timedelta(minutes=10 * i + 1),
                    **values
                )
            )

        return history
'''

if old not in source:
    raise SystemExit("Expected make_history function not found. No changes made.")

backup = path.with_suffix(".py.step_14_6_7_4_1.backup")
backup.write_text(source, encoding="utf-8")

path.write_text(
    source.replace(old, new, 1),
    encoding="utf-8"
)

print("TEST FIXTURE UPDATED")
print("BACKUP:", backup)
