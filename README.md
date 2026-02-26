# Session Handoff — Claude Code Skill

File-based session continuity for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Save your working context before closing a session and resume exactly where you left off.

## Why?

Claude Code conversations lose context when they end. Long sessions hit context limits and silently drop earlier details. This skill solves both problems:

- **Save** captures your goal, progress, open items, and key files into a compact handoff file
- **Resume** restores that context in a new session so you can pick up without re-explaining everything

## Install

```bash
claude skill install gh:Internet-Marketing-Agentur/cc-skill-session-handoff
```

## Usage

### Save a session

Say any of these to Claude Code:

> "save session" · "handoff" · "speichern" · "continue later"

Claude analyzes the conversation and writes a structured `HANDOFF.md` to your project's memory directory. The content is also copied to your clipboard.

### Resume a session

Say any of these:

> "resume" · "weitermachen" · "fortsetzen" · "letzte session"

Claude reads the handoff file, presents a summary, and asks what to work on next.

### Proactive behavior

- **At session start:** If a handoff file exists, Claude automatically offers to resume
- **During long sessions:** Claude suggests saving before context gets lost

## How it works

The skill writes a structured markdown file (`memory/HANDOFF.md`) with these sections:

| Section | Purpose |
|---|---|
| **Context** | 1–2 sentence goal statement |
| **Progress** | Completed items with outcomes |
| **Current State** | Exact point to resume from |
| **Key Files** | Paths and their roles |
| **Open Items** | Checklist of next actions |
| **Constraints/Decisions** | Established decisions and rationale |

The file is sized adaptively — ~100 tokens for a quick bug fix, up to ~800 for complex multi-system work. General knowledge Claude already has is excluded; only hard-to-rediscover specifics (file paths, error messages, decisions) are kept.

## Example

After saving:

```markdown
<!-- Session Handoff — 2026-02-26 15:30 -->

## Context
Optimierung des Produktimporter-Workflows für SEO-Artikeltext-Generierung mit Claude Sonnet 4.6.

## Progress
- System-Prompt erweitert (PAS, FAQ, LLMO, Buybox-Format)
- Claude Sonnet 4.6 via OpenRouter angebunden
- Parse JSON Output Node eingefügt

## Current State
3-Wege-Vergleich abgeschlossen. Sonnet als Standard gewählt.

## Key Files
- `backup/vergleich-3-wege.html` - Modellvergleich
- `backup/system-prompt-2026-02-26.txt` - Prompt Backup

## Open Items
- [ ] Produktionstest mit mehreren Produkten
- [ ] Temperature-Einstellungen optimieren

## Constraints/Decisions
- Sonnet 4.6 als Standard (Opus ~5x teurer, marginaler Qualitätsgewinn)
```

After resuming, Claude presents a summary and asks where to continue.

## File structure

```
session/
├── SKILL.md          # Skill definition (loaded by Claude Code)
├── README.md
├── assets/           # Asset files (templates, images, etc.)
├── references/       # Reference documentation
└── scripts/          # Helper scripts
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI

## License

MIT

## Author

Achim Dräger — [Internet Marketing Agentur](https://www.internet-marketing-agentur.com)
