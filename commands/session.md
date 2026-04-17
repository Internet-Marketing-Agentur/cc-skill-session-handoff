---
description: Save, resume, or view session handoff history
argument-hint: "[save|resume|history] [--learn|--no-learn]"
---

Invoke the `session` skill with arguments: $ARGUMENTS

Mode selection:
- `save` or empty with context-save intent → SAVE mode
- `save --learn` → SAVE mode, force extraction of decisions/insights even if heuristics find none
- `save --no-learn` → SAVE mode, skip extraction entirely
- `save` (no flag) → SAVE mode with **auto-detect**: scans the session for stable knowledge candidates and asks once if any are found
- `resume` → RESUME mode
- `history` → HISTORY mode

If no arguments are given, fall back to the skill's auto-detect behavior (offer resume if HANDOFF.md exists, otherwise prompt).
