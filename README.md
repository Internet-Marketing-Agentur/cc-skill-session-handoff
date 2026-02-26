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
Adding OAuth2 login flow to the FastAPI backend with Google and GitHub providers.

## Progress
- Google OAuth2 working (login, callback, token exchange)
- User model extended with `provider` and `provider_id` fields
- Alembic migration created and applied
- Frontend redirect to /auth/google/login working

## Current State
Google flow complete. GitHub OAuth2 started — callback endpoint returns 401,
likely a scope issue with the GitHub app configuration.

## Key Files
- `src/auth/oauth.py` - OAuth route handlers
- `src/models/user.py` - User model with provider fields
- `alembic/versions/a3f8...py` - Migration for provider columns
- `.env.example` - Updated with GITHUB_CLIENT_ID/SECRET placeholders

## Open Items
- [ ] Debug GitHub callback 401 (check scopes in GitHub app settings)
- [ ] Add logout endpoint that revokes OAuth tokens
- [ ] Write tests for both OAuth flows

## Constraints/Decisions
- Using authlib over requests-oauthlib (better async support)
- Storing provider tokens encrypted, not plain text
```

After resuming, Claude presents a summary and asks where to continue.

## File structure

```
session/
├── SKILL.md          # Skill definition (loaded by Claude Code)
├── README.md
└── LICENSE
```

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI

## License

MIT

## Author

Achim Dräger — [Internet Marketing Agentur](https://www.internet-marketing-agentur.com)
