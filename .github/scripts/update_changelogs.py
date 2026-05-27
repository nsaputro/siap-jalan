"""
Post-release changelog updater.

Called by the Release workflow after a new version tag is pushed.
Reads VERSION, NEXT_VERSION, TODAY, OLD_TAG, REPO from environment variables.

Actions performed:
  1. CHANGELOG.md — replaces the [Unreleased] heading with
     [Unreleased] — next: NEXT_VERSION  +  [VERSION] - TODAY
  2. CHANGELOG.md — updates the comparison links at the bottom
  3. ha-addon/CHANGELOG.md — extracts the new VERSION section and
     converts Keep-a-Changelog categories into compact "- Cat: item" bullets
"""
import os
import pathlib
import re

VERSION = os.environ["VERSION"]
NEXT_VERSION = os.environ["NEXT_VERSION"]
TODAY = os.environ["TODAY"]
OLD_TAG = os.environ["OLD_TAG"]
REPO = os.environ["REPO"]

changelog = pathlib.Path("CHANGELOG.md").read_text()

# Replace any [Unreleased] heading with the released section + fresh [Unreleased]
changelog = re.sub(
    r"## \[Unreleased\][^\n]*",
    f"## [Unreleased] — next: {NEXT_VERSION}\n\n## [{VERSION}] - {TODAY}",
    changelog,
    count=1,
)

# Update comparison links at the bottom
changelog = re.sub(
    r"\[Unreleased\]: https://[^\n]+",
    (
        f"[Unreleased]: https://github.com/{REPO}/compare/v{VERSION}...HEAD\n"
        f"[{VERSION}]: https://github.com/{REPO}/compare/{OLD_TAG}...v{VERSION}"
    ),
    changelog,
)
pathlib.Path("CHANGELOG.md").write_text(changelog)

# ── Build ha-addon/CHANGELOG.md from the newly-created VERSION section ──────
m = re.search(
    rf"## \[{re.escape(VERSION)}\] - {re.escape(TODAY)}\n(.*?)(?=\n## \[)",
    changelog,
    re.DOTALL,
)
entries_raw = m.group(1).strip() if m else ""

# Convert Keep-a-Changelog sections into compact "- Category: item" bullets
lines: list[str] = []
category: str | None = None
for line in entries_raw.splitlines():
    if line.startswith("### "):
        category = line[4:].strip()
    elif line.startswith("- ") and category:
        lines.append(f"- {category}: {line[2:]}")

ha = f"## {VERSION}\n\n" + "\n".join(lines)
ha += f"\n\n---\n\n[Full changelog](https://github.com/{REPO}/blob/main/CHANGELOG.md)\n"
pathlib.Path("ha-addon/CHANGELOG.md").write_text(ha)
