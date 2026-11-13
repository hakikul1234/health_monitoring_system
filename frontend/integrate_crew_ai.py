from pathlib import Path
import re

page = Path("src/features/crew/CrewHealthPage.jsx")

content = page.read_text(encoding="utf-8-sig")

import_line = 'import useCrewHealthStore from "./crewHealthStore";'

assert content.count(import_line) == 1, (
    "Expected Crew Health store import was not found exactly once."
)

content = content.replace(
    import_line,
    import_line + '\nimport CrewReadingAnalysis from "./CrewReadingAnalysis";',
    1
)

pattern = r'([ \t]*<div className="crew-reading-time">.*?</div>)'

matches = list(re.finditer(pattern, content, flags=re.DOTALL))

assert len(matches) == 1, (
    f"Expected exactly one reading-time section, found {len(matches)}."
)

match = matches[0]

replacement = (
    match.group(1)
    + '\n\n                      <CrewReadingAnalysis readingId={reading.id} />'
)

content = (
    content[:match.start()]
    + replacement
    + content[match.end():]
)

page.write_text(content, encoding="utf-8")

print("CREW HEALTH PAGE UPDATED")
print("AI COMPONENT IMPORT: VERIFIED")
print("READING ANALYSIS COMPONENT: CONNECTED")
