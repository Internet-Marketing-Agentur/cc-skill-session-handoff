# Session Handoff — Claude Code Skill

File-based session continuity for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Save your working context before closing a session and resume exactly where you left off.

## Why?

Every Claude Code session builds up valuable context — file paths discovered, decisions made, bugs diagnosed, approaches tried. When the session ends, all of that is lost. The next session starts from zero and has to rediscover everything.

This skill solves that by separating two kinds of knowledge:

- **Session state** (HANDOFF.md) — ephemeral: current task, open items, key files, dead ends. Consumed by the next session, then archived.
- **Project knowledge** (CLAUDE.md) — persistent: architecture, conventions, discoveries, gotchas. Available in every session automatically.

Every save auto-detects stable insights from the session and routes them into CLAUDE.md (after confirmation) and DECISIONS.md. The `--learn` / `--no-learn` flags override the heuristic when needed. A `CLAUDE.md.template` is included to help structure your project knowledge.

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/Internet-Marketing-Agentur/cc-skill-session-handoff.git \
  ~/.claude/skills/session
```

Then restart Claude Code (or run `/reload-plugins`) and the skill is available.

### Update

```bash
cd ~/.claude/skills/session && git pull
```

## Usage

### Save a session

Say any of these to Claude Code:

> "save session" · "handoff" · "speichern" · "continue later" · "save"

Claude reviews the entire conversation — not just the last few exchanges — and writes a structured `HANDOFF.md` to `<project-root>/.claude/memory/HANDOFF.md`. The content is also copied to your clipboard (macOS, Linux X11, and Wayland supported). If the project is a git repo, Claude ensures `.claude/memory/` is in `.gitignore` (creating the file if none exists) — handoffs can contain sensitive context and should not be committed.

#### Learning extraction (auto-detect by default)

By default, every save scans the session for **stable project knowledge** — architectural decisions, discoveries, conventions, setup quirks. If candidates are found, Claude asks once whether to log them; if nothing is found, it stays silent. No flag needed.

To override the auto-detect:

| Flag / phrase | Behavior |
|---|---|
| `/session save --learn` · "save with learnings" · "speicher mit lernen" | Force extraction even if heuristics find nothing |
| `/session save --no-learn` · "skip learnings" · "ohne lernen" | Suppress extraction completely |

When learning is active, candidates route to:

- **Decisions** → `<project-root>/DECISIONS.md` (appended automatically — date, decision, rationale, alternatives)
- **Insights** → `<project-root>/CLAUDE.md` (architecture, conventions, gotchas — only after your confirmation)

This keeps HANDOFF.md lean (session state only) while ensuring project knowledge isn't lost.

### Resume a session

Say any of these:

> "resume" · "load" · "weitermachen" · "fortsetzen" · "pick up" · "where did we leave off" · "last session"

Claude reads the handoff file, shows a summary, and asks what to work on next. The handoff file is then archived to prevent duplicate resume offers.

### View session history

> `/session history` · "session history" · "past sessions"

Shows a timeline of all archived sessions with date, goal, and status. Useful for recalling what happened across multiple sessions.

### Proactive behavior

- **At session start:** If a handoff file exists, Claude offers to resume — with a staleness hint if the handoff is more than a week old
- **During long sessions:** Claude suggests saving before context gets lost

## How it works

The skill writes a structured markdown file (`memory/HANDOFF.md`) with these sections:

| Section | Purpose |
|---|---|
| **Context** | Goal statement |
| **Current State** | Exact point to resume from |
| **Key Files** | Paths and what changed |
| **Open Items** | Checklist of next actions |
| **Dead Ends** | Approaches tried and abandoned (prevents repeating them) |
| **Decisions** | Choices made and why |

Project-level knowledge belongs elsewhere — every save auto-detects candidates and routes them:

- **Decisions** → `<project-root>/DECISIONS.md` (appended automatically — date, decision, rationale, alternatives)
- **Architecture, conventions, gotchas** → `<project-root>/CLAUDE.md` (loaded every session, only after your confirmation)

The save process is git-aware — it runs `git diff --stat` and `git status` to capture file changes that weren't explicitly discussed in conversation.

The file is sized adaptively — ~250 tokens for a quick bug fix, up to ~1500 for complex multi-system work. The skill errs toward completeness: a longer handoff that captures everything is more valuable than a short one that forces the next session to rediscover context.

The skill responds in the user's language — it adapts automatically to English, German, or whatever language the conversation is in.

## Example

After saving:

```markdown
<!-- Session Handoff — 2026-02-26 15:30 -->

## Context
Adding OAuth2 login flow (Google + GitHub) to FastAPI SaaS backend.

## Current State
Google OAuth complete. GitHub callback returns 401 —
likely scope issue in GitHub app config, not code.

## Key Files
- `src/auth/oauth.py` - OAuth handlers (Google working, GitHub WIP)
- `src/models/user.py` - User model with provider fields
- `alembic/versions/a3f8...py` - Migration for provider columns

## Open Items
- [ ] Fix GitHub callback 401 — check scopes in GitHub app settings
- [ ] Add logout endpoint (authlib has `revoke_token()`)
- [ ] Write tests for both OAuth flows (mock with `respx`)

## Dead Ends
- Debugged GitHub 401 as code issue for ~20 min — it's a config issue

## Decisions
- authlib over requests-oauthlib (async support, less boilerplate)
- Provider tokens encrypted via cryptography.fernet
```

After resuming, Claude presents a summary and asks where to continue.

## File structure

```
cc-skill-session-handoff/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (name, version, author)
├── commands/
│   └── session.md               # Slash command: /session [save|resume|history] [--learn|--no-learn]
├── scripts/
│   └── session_helper.py        # Python helper (paths, archive, gitignore, migrate, list)
├── SKILL.md                     # Skill definition (loaded by Claude Code)
├── CLAUDE.md.template           # Template for persistent project knowledge
├── DECISIONS.md.template        # Template for decision log (on-demand, auto-maintained)
├── README.md
└── LICENSE
```

The Python helper collapses the deterministic parts (path resolution, existence checks, archive renaming, gitignore updates, legacy file migration, history listing) into a single subprocess call per operation. It returns JSON for Claude to consume, which keeps the skill fast and token-efficient. Python 3 standard library only — no dependencies.

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI

## License

MIT

## Author

Achim Dräger — [Internet Marketing Agentur](https://www.internet-marketing-agentur.com)
