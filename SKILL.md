---
name: session
description: >
  Session continuity with file-based handoff. Two modes: save and resume.
  SAVE: Use when (1) approaching context limits, (2) user says "handoff", "save", "save session",
  "continue later", or similar, (3) before closing a session with unfinished work.
  Writes memory/HANDOFF.md + copies to clipboard.
  RESUME: Use when (1) user says "resume", "hand-on", "weitermachen", "letzte session",
  (2) PROACTIVELY at conversation start if memory/HANDOFF.md exists — offer to resume.
  PROACTIVE: (1) If memory/HANDOFF.md exists at session start, immediately offer resume.
  (2) When context window is getting large, suggest save before information is lost.
---

# Session Handoff

File-based session continuity with save and resume modes.

## Mode Detection

Determine mode from user input:
- **save**: User says "handoff", "save", "speichern", "session-handoff save", or context is running low
- **resume**: User says "resume", "hand-on", "weitermachen", "fortsetzen", "session-handoff resume"
- **auto-detect**: If HANDOFF.md exists in memory directory and no explicit mode given, offer resume

If mode is ambiguous, ask the user.

---

## Mode: SAVE

### Step 1: Analyze Current Session

Identify and categorize:

- **Goal state**: What is the user trying to accomplish? What's the end state?
- **Current progress**: What's been done? What's working?
- **Blockers/open questions**: What's unresolved? What decisions are pending?
- **Key artifacts**: Files modified, commands run, errors encountered
- **Critical context**: Domain knowledge, constraints, or preferences established

### Step 2: Apply Token Efficiency Heuristics

**Include:**
- Specific file paths, function names, error messages (hard to rediscover)
- Decisions made and their rationale (prevents re-discussion)
- Current hypothesis or approach being tested
- Exact reproduction steps for bugs
- IDs, URLs, credentials references (not values) that are needed to continue

**Exclude:**
- General knowledge Claude already has
- Verbose explanations of standard concepts
- Full file contents (use paths + line numbers instead)
- Conversation pleasantries or meta-discussion

**Compress:**
- Use bullet points over prose
- Reference files by path, not content
- Summarize long error traces to key lines
- Use "established: X" for agreed-upon decisions

### Step 3: Adaptive Sizing

**Simple tasks** (bug fix, small feature): 100-200 tokens
- Goal, current file, error/behavior, next step

**Medium tasks** (feature implementation, refactor): 200-400 tokens
- Goal, progress list, current state, key files, next steps

**Complex tasks** (architecture, multi-system): 400-800 tokens
- Full structure, plus constraints and decision rationale

### Step 4: Write HANDOFF.md

Write the handoff to `{memory_directory}/HANDOFF.md` using this structure:

```markdown
<!-- Session Handoff — {YYYY-MM-DD HH:MM} -->

## Context
[1-2 sentence goal statement]

## Progress
- [Completed item with outcome]
- [Completed item with outcome]

## Current State
[What's happening right now - the exact point to resume from]

## Key Files
- `path/to/file.ext` - [role/status]

## Open Items
- [ ] [Next immediate action]
- [ ] [Subsequent action]

## Constraints/Decisions
- [Established constraint or decision]
```

### Step 5: Copy to Clipboard and Display

**Always do all three:**

1. **Write the file** to `{memory_directory}/HANDOFF.md`
2. **Display the full prompt** in a fenced code block so the user can see it
3. **Copy to clipboard** using `pbcopy`:

```bash
cat "{memory_directory}/HANDOFF.md" | pbcopy
```

Confirm with: "Session gespeichert in `memory/HANDOFF.md` und in die Zwischenablage kopiert."

---

## Mode: RESUME

### Step 1: Read Handoff Data

1. Read `{memory_directory}/HANDOFF.md`
2. Read `{memory_directory}/MEMORY.md` for additional project context
3. If HANDOFF.md does not exist, inform the user: "Keine Handoff-Datei gefunden. Starte eine frische Session."

### Step 2: Display Summary

Present a concise summary to the user:

```
## Letzte Session

**Ziel:** [Context from handoff]
**Stand:** [Current state]

### Erledigt
- [Progress items]

### Offene Punkte
- [ ] [Open item 1]
- [ ] [Open item 2]

### Relevante Dateien
- `path` - [role]
```

### Step 3: Ask What To Do

Ask the user: "Womit soll ich weitermachen?"

Use AskUserQuestion if there are distinct open items to choose from. Otherwise, ask as free text.

### Step 4: Archive Handoff

After successfully loading the handoff, archive the file:

```bash
mv "{memory_directory}/HANDOFF.md" "{memory_directory}/HANDOFF-{YYYY-MM-DD}.md"
```

This prevents the same handoff from being offered again at the next session start.

---

## Proactive Behavior

### At Session Start
If `{memory_directory}/HANDOFF.md` exists, proactively inform the user:

> "Ich habe eine Handoff-Datei von der letzten Session gefunden. Soll ich dort weitermachen wo wir aufgehört haben?"

If user confirms, execute RESUME mode. If user declines, continue normally.

### When Context Gets Large
When the conversation has been going on for a while and significant work has been done, suggest:

> "Die Session ist schon recht umfangreich. Soll ich einen Handoff speichern, bevor Kontext verloren geht?"

---

## Important Rules

- **MEMORY.md is read-only** for this skill. Never modify MEMORY.md — it is managed separately by the auto-memory system.
- **HANDOFF.md is ephemeral** — it represents a single session transition, not persistent knowledge.
- Stable, long-term learnings belong in MEMORY.md (managed outside this skill). Session-specific state belongs in HANDOFF.md.
- Always use the project's auto-memory directory path for file operations.
- If both MEMORY.md and HANDOFF.md exist during resume, use MEMORY.md for background context and HANDOFF.md for the specific resume point.

---

## Example: Save

```markdown
<!-- Session Handoff — 2026-02-26 15:30 -->

## Context
Optimierung des Neptunmaster Produktimporter n8n-Workflows für SEO-Artikeltext-Generierung mit Claude Sonnet 4.6.

## Progress
- System-Prompt erweitert (PAS, FAQ, LLMO, Buybox-Format, Checkliste)
- Claude Sonnet 4.6 via OpenRouter angebunden
- Parse JSON Output Node eingefügt (strippt Markdown-Fences)
- Update row in sheet Expressions gefixt

## Current State
3-Wege-Vergleich (GPT-4.1 vs Sonnet vs Opus) abgeschlossen. Sonnet als Standard gewählt. HTML-Vergleich erstellt.

## Key Files
- `backup/vergleich-3-wege.html` - 3-Wege-Modellvergleich
- `backup/system-prompt-2026-02-26.txt` - Original-Prompt Backup

## Open Items
- [ ] Produktionstest mit mehreren Produkten
- [ ] LLM-Einstellungen (Temperature) für Sonnet optimieren
- [ ] Output Artikeltitel Feld klären

## Constraints/Decisions
- Sonnet 4.6 als Standard (Opus ~5x teurer, marginaler Qualitätsgewinn)
- updateNode ersetzt gesamten parameters-Block — immer alle Felder mitgeben
```

## Example: Resume Output

```
## Letzte Session

**Ziel:** Optimierung des Neptunmaster Produktimporter n8n-Workflows für SEO-Artikeltext-Generierung
**Stand:** 3-Wege-Vergleich abgeschlossen, Sonnet als Standard gewählt

### Erledigt
- System-Prompt erweitert (PAS, FAQ, LLMO, Buybox-Format, Checkliste)
- Claude Sonnet 4.6 via OpenRouter angebunden
- Parse JSON Output Node eingefügt
- Update row in sheet Expressions gefixt

### Offene Punkte
- [ ] Produktionstest mit mehreren Produkten
- [ ] LLM-Einstellungen (Temperature) für Sonnet optimieren
- [ ] Output Artikeltitel Feld klären

Womit soll ich weitermachen?
```
