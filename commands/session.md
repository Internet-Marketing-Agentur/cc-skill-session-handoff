---
description: Save, resume, or view session handoff history
argument-hint: "[save|resume|history] [--learn]"
---

Invoke the `session` skill with arguments: $ARGUMENTS

Mode selection:
- `save` or empty with context-save intent → SAVE mode
- `save --learn` → SAVE mode with `--learn` enabled (also update DECISIONS.md and suggest CLAUDE.md additions)
- `resume` → RESUME mode
- `history` → HISTORY mode

If no arguments are given, fall back to the skill's auto-detect behavior (offer resume if HANDOFF.md exists, otherwise prompt).
