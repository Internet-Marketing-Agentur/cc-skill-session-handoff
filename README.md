# Session Handoff — Claude Code Skill

File-based session continuity for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Save your working context before closing a session and resume exactly where you left off.

## Why?

Every Claude Code session builds up valuable context — file paths discovered, decisions made, bugs diagnosed, approaches tried. When the session ends, all of that is lost. The next session starts from zero and has to rediscover everything.

This skill solves that by capturing session state into a compact handoff file that lets the next session skip the rediscovery phase entirely.

## Install

```bash
claude skill install gh:Internet-Marketing-Agentur/cc-skill-session-handoff
```

## Usage

### Save a session

Say any of these to Claude Code:

> "save session" · "handoff" · "speichern" · "continue later" · "save"

Claude analyzes the conversation, extracts hard-to-rediscover context, and writes a structured `HANDOFF.md` to your project's memory directory. The content is also copied to your clipboard (macOS, Linux X11, and Wayland supported).

### Resume a session

Say any of these:

> "resume" · "load" · "weitermachen" · "fortsetzen" · "pick up" · "where did we leave off" · "last session"

Claude reads the handoff file, shows a summary, and asks what to work on next. The handoff file is then archived to prevent duplicate resume offers.

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
| **Constraints/Decisions** | Decisions and why they were made |

The file is sized adaptively — ~100 tokens for a quick bug fix, up to ~800 for complex multi-system work. Only hard-to-rediscover specifics are kept (file paths, error messages, decisions with rationale). General knowledge Claude already has is excluded.

The skill responds in the user's language — it adapts automatically to English, German, or whatever language the conversation is in.

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
cc-skill-session-handoff/
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
