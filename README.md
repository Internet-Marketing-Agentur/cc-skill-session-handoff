# Session Handoff — Claude Code Skill

File-based session continuity for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Save your working context before closing a session and resume exactly where you left off.

## Why?

Every Claude Code session builds up valuable context — file paths discovered, decisions made, bugs diagnosed, approaches tried. When the session ends, all of that is lost. The next session starts from zero and has to rediscover everything.

This skill solves that by separating two kinds of knowledge:

- **Session state** (HANDOFF.md) — ephemeral: current task, open items, key files, dead ends. Consumed by the next session, then archived.
- **Project knowledge** (CLAUDE.md) — persistent: architecture, conventions, discoveries, gotchas. Available in every session automatically.

The `--learn` option bridges the two by extracting stable insights from a session into CLAUDE.md. A `CLAUDE.md.template` is included to help structure your project knowledge.

## Install

```bash
claude skill install gh:Internet-Marketing-Agentur/cc-skill-session-handoff
```

## Usage

### Save a session

Say any of these to Claude Code:

> "save session" · "handoff" · "speichern" · "continue later" · "save"

Claude reviews the entire conversation — not just the last few exchanges — and writes a structured `HANDOFF.md` to your project's memory directory. The content is also copied to your clipboard (macOS, Linux X11, and Wayland supported).

#### `--learn` option

> "save session with learn" · `/session save --learn`

When enabled, Claude extracts stable knowledge from the session and routes it to the right place:

- **Decisions** → `DECISIONS.md` (appended automatically — date, decision, rationale, alternatives)
- **Insights** → `CLAUDE.md` (architecture, conventions, gotchas — only after your confirmation)

This keeps HANDOFF.md lean (session state only) while ensuring project knowledge isn't lost.

### Continuous decision capture

When your project's `CLAUDE.md` includes the "Decision & Learning Trail" rule (from the included template), Claude logs decisions, discoveries, and course corrections to `DECISIONS.md` **in real-time as they happen** — not just at save time.

This means:
- Decisions are captured when reasoning is fresh
- Nothing is lost if the session ends unexpectedly
- You get a traceable trail of *why* your project looks the way it does

Three entry types are supported:

| Type | Example |
|---|---|
| **Decision** | "authlib over requests-oauthlib — better async support" |
| **Learning** | "Auth middleware swallows errors silently — causes subtle bugs" |
| **Course Correction** | "Switched from REST to GraphQL — N+1 queries were unmanageable" |

The `--learn` flag at save time acts as a safety net — it catches anything that wasn't logged in real-time.

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

Project-level knowledge belongs elsewhere:

- **Decisions, learnings, course corrections** → `DECISIONS.md` (logged in real-time during the session, with `--learn` as safety net)
- **Architecture, conventions, gotchas** → `CLAUDE.md` (loaded every session, updated via `--learn`)

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
session/
├── SKILL.md              # Skill definition (loaded by Claude Code)
├── CLAUDE.md.template    # Template for persistent project knowledge
├── DECISIONS.md.template # Template for decision log (on-demand, auto-maintained)
├── README.md
└── LICENSE
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI

## License

MIT

## Author

Achim Dräger — [Internet Marketing Agentur](https://www.internet-marketing-agentur.com)
