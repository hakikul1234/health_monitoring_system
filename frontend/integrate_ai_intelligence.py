from pathlib import Path
import shutil

path = Path("src/features/dashboard/DashboardPage.jsx")

source = path.read_text(encoding="utf-8")

backup = path.with_suffix(".jsx.step-14-6-6-2.backup")
shutil.copy2(path, backup)

old_import = (
    'const SimulatorPage = lazy(() => import("../simulator/SimulatorPage"));'
)

new_import = old_import + '\n' + (
    'const AIIntelligencePage = lazy(() => import("./AIIntelligencePage"));'
)

if "const AIIntelligencePage = lazy(" not in source:
    if old_import not in source:
        raise SystemExit("ERROR: Simulator lazy import not found.")
    source = source.replace(old_import, new_import, 1)

old_branch = '''        ) : activePage === "Simulator" ? (
          <Suspense fallback={<LazyPageFallback />}>
            <SimulatorPage />
          </Suspense>
        ) : (
'''

new_branch = '''        ) : activePage === "Simulator" ? (
          <Suspense fallback={<LazyPageFallback />}>
            <SimulatorPage />
          </Suspense>
        ) : activePage === "AI Intelligence" ? (
          <Suspense fallback={<LazyPageFallback />}>
            <AIIntelligencePage />
          </Suspense>
        ) : (
'''

if '<AIIntelligencePage />' not in source:
    if old_branch not in source:
        raise SystemExit("ERROR: Simulator navigation branch not found.")
    source = source.replace(old_branch, new_branch, 1)

path.write_text(source, encoding="utf-8")

print("AI INTELLIGENCE LAZY IMPORT: CONNECTED")
print("AI INTELLIGENCE NAVIGATION BRANCH: CONNECTED")
print("BACKUP CREATED:", backup)
