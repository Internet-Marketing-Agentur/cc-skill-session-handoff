# Session Handoff — Claude Code Skill

File-based session continuity for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Save your working context before closing a session and resume exactly where you left off.

## Why?

Every Claude Code session builds up valuable context — file paths discovered, decisions made, bugs diagnosed, approaches tried. When the session ends, all of that is lost. The next session starts from zero and has to rediscover everything.

This skill solves that by separating two kinds of knowledge:

- **Session state** (HANDOFF.md) — ephemeral: current task, open items, key files, dead ends. Consumed by the next session, then archived.
- **Project knowledge** (CLAUDE.md) — persistent: architecture, conventions, discoveries, gotchas. Available in every session automatically.

The `--learn` option bridges the two by extracting stable insights from a session into CLAUDE.md. A `CLAUDE.md.template` is included to help structure your project knowledge.

## Install

Claude Code plugins install via the `/plugin` slash command — not a CLI flag. From inside a Claude Code session:

```
/plugin marketplace add Internet-Marketing-Agentur/cc-skill-session-handoff
/plugin install cc-skill-session-handoff@Internet-Marketing-Agentur-cc-skill-session-handoff
```

Or interactively:

1. Run `/plugin`
2. Go to **Marketplaces** → add `Internet-Marketing-Agentur/cc-skill-session-handoff`
3. Go to **Discover** → find this plugin → install

After install, restart the session once so Claude Code picks up the skill and the `/session` command.

## Usage

### Save a session

Say any of these to Claude Code:

> "save session" · "handoff" · "save context" · "session speichern" · "continue later" · `/session save`

Bare "save" / "speichern" is **not** a trigger — it would collide with "save the file". The phrase has to reference the session or context.

Claude reviews the entire conversation, runs a git snapshot (branch, status, diff-stat, unpushed commits, stashes), and writes a structured `HANDOFF.md`. The content is also copied to your clipboard — macOS (`pbcopy`), Linux X11 (`xclip`), Linux Wayland (`wl-copy`), and Windows / WSL / Git Bash (`clip.exe`) are all supported.

#### `--learn` option

> "save session with learn" · `/session save --learn`

When enabled, Claude extracts stable knowledge from the session and routes it to the right place:

- **Decisions** → `DECISIONS.md` (appended automatically — date, decision, rationale, alternatives). Existing entries are read first and deduplicated: exact matches are skipped, refinements/reversals are appended with a `Supersedes:` cross-reference, and the log stays append-only.
- **Insights** → `CLAUDE.md` (architecture, conventions, gotchas — only after your confirmation)

This keeps HANDOFF.md lean (session state only) while ensuring project knowledge isn't lost.

### Resume a session

Say any of these:

> "resume" · "resume session" · "load session" · "weitermachen" · "fortsetzen" · "pick up where we left off" · "where did we leave off" · "last session" · `/session resume`

Claude reads the handoff file and shows a summary. Archiving happens **only after you actually continue** — pick an open item, ask a follow-up, or say "let's continue". If you say "start fresh" instead, the handoff stays in place (or is deleted on request) rather than silently disappearing.

### View session history

> `/session history` · "session history" · "past sessions"

Shows a timeline of all archived sessions with date, goal, and status. Useful for recalling what happened across multiple sessions.

### Proactive behavior

- **At session start:** If a handoff file exists, Claude offers to resume — with a staleness hint if the handoff is more than a week old
- **During long sessions:** Claude suggests saving before context gets lost

## How it works

The skill writes a structured markdown file (`HANDOFF.md`) with these sections:

| Section | Purpose |
|---|---|
| **Context** | Goal statement |
| **Current State** | Exact point to resume from |
| **Key Files** | Paths and what changed |
| **Open Items** | Checklist of next actions |
| **Dead Ends** | Approaches tried and abandoned (prevents repeating them) |
| **Decisions** | Choices made and why |

Project-level knowledge belongs elsewhere — use `--learn` to extract it:

- **Decisions** → `DECISIONS.md` (on-demand read, auto-maintained via CLAUDE.md rule)
- **Architecture, conventions, gotchas** → `CLAUDE.md` (loaded every session)

### Where files are stored

`{memory_directory}` resolves in this order, stopping at the first that applies:

1. An explicit path you give in the request (e.g. "save to `docs/sessions/`")
2. `$CLAUDE_MEMORY_DIR` if set in the environment
3. `.claude/memory/` relative to the git top-level (or CWD if not a git repo)

Archived handoffs are named `HANDOFF-YYYY-MM-DD-HHMM.md` so multiple saves per day don't collide.

### Git awareness

The save process captures repo state the conversation may not have surfaced: current branch, `git status --short`, `git diff --stat`, unpushed commits (`@{upstream}..HEAD`), and `git stash list`. Branches, local-only commits, and stashes are the details you'd otherwise rediscover the hard way.

### Language

The conversational wrapper (summaries, confirmations, questions) matches the language of your message — German in, German out. The **contents of HANDOFF.md** stay in English for cross-tool consistency.

### Size

The file is sized adaptively — ~250 tokens for a quick bug fix, up to ~1500 for complex multi-system work. The skill errs toward completeness: a longer handoff that captures everything beats a short one that forces rediscovery.

### Security

Handoffs can contain error messages with tokens, internal paths, or other sensitive strings. If the resolved memory directory sits inside your repo, add `**/HANDOFF*.md` (or the matching pattern) to `.gitignore` before your first commit.

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
│   └── plugin.json        # Plugin manifest (name, version, author)
├── commands/
│   └── session.md         # Slash command: /session [save|resume|history] [--learn]
├── SKILL.md               # Skill definition (loaded by Claude Code)
├── CLAUDE.md.template     # Template for persistent project knowledge
├── DECISIONS.md.template  # Template for decision log (on-demand, auto-maintained)
├── README.md
└── LICENSE
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI

## License

MIT

## Author

Achim Dräger — [Internet Marketing Agentur](https://www.internet-marketing-agentur.com)
