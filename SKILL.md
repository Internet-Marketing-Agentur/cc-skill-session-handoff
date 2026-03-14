---
name: session
description: >
  Session continuity with file-based handoff — saves and restores context across Claude Code sessions.
  Use this skill whenever the user wants to save, store, persist, or hand off their current session state,
  or when they want to resume, continue, restore, or pick up where they left off.
  Trigger words: "handoff", "save session", "speichern", "save", "continue later", "resume",
  "weitermachen", "load", "fortsetzen", "pick up", "where did we leave off", "last session",
  "session history", "past sessions".
  Also trigger PROACTIVELY: (1) at session start if memory/HANDOFF.md exists — offer to resume,
  (2) when context window is getting large — suggest saving before information is lost.
  Even if the user doesn't explicitly mention "session" or "handoff", trigger this skill whenever
  they clearly want to preserve work for later or restore previous work.
---

# Session Handoff

Preserve session context across conversation boundaries so the next session can pick up exactly where this one left off.

The core idea: a session produces knowledge that's expensive to rebuild — file paths discovered, decisions made, bugs diagnosed, approaches tried and rejected. HANDOFF.md captures this perishable context in a compact format that lets the next session skip the rediscovery phase entirely.

## Parameters

- **learn** (default: off): When enabled, the save process also identifies discoveries and decisions that belong in CLAUDE.md rather than HANDOFF.md, and suggests appending them. Usage: `/session save --learn` or "save session with learn"

## Mode Detection

Determine mode from user input:
- **save**: "handoff", "save", "speichern", "continue later", "save session", or context is running low
- **resume**: "resume", "load", "weitermachen", "fortsetzen", "pick up", "where did we leave off", "last session"
- **history**: "session history", "past sessions", "session log", `/session history`
- **auto-detect**: If `{memory_directory}/HANDOFF.md` exists and no explicit mode given, offer resume

If ambiguous, ask the user.

---

## Mode: SAVE

### Step 1: Analyze the Session

Review the entire conversation — not just the last few exchanges. Also run `git diff --stat` and `git status` to capture file changes that may not have been explicitly discussed. Identify what would be most expensive for a fresh session to rediscover:

- **Goal**: What's the user trying to accomplish? What's the bigger picture?
- **Project context**: What did we learn about the project structure, tech stack, architecture, quirks? Things that aren't obvious from the code alone.
- **Session timeline**: What happened in what order? Include approaches that were tried and abandoned — a fresh session shouldn't repeat dead ends.
- **Discoveries**: Surprising findings, undocumented behavior, gotchas ("the API uses GraphQL internally despite REST docs", "tests require Docker running")
- **Current state**: The exact point to resume from — what was just tried, what's next
- **Key artifacts**: Combine files mentioned in conversation with `git diff --stat` output. This catches files that were edited but never explicitly discussed.
- **Blockers**: Unresolved issues, pending decisions
- **Decisions**: Choices made during the session and why

### Step 2: Compress Intelligently

The goal is information density — but err on the side of including too much rather than too little. A handoff that's too brief forces the next session to rediscover context, which is the exact problem this skill exists to solve.

A fresh Claude session already knows general programming concepts, standard library APIs, and common patterns — don't repeat those. Focus on what's unique to *this project* and *this session*:

**High value** (include): project-specific architecture, file paths, function names, error messages, decisions with rationale, dead ends and why they failed, current hypothesis, reproduction steps, relevant IDs/URLs, discovered quirks

**Low value** (omit): general programming knowledge, verbose explanations of standard concepts, full file contents (use path + line numbers), conversation meta-discussion

**Format**: bullet points over prose, paths over content, key error lines over full traces

### Step 3: Size to Complexity

Err toward completeness. Target token ranges:

- **Simple tasks** (single bug fix, small change): 250-400 tokens
- **Medium tasks** (feature implementation, refactor): 400-800 tokens
- **Complex tasks** (architecture, multi-system, exploration): 800-1500 tokens

If in doubt, go longer. A 1200-token handoff that captures everything is far more valuable than a 300-token one that forces rediscovery.

### Step 4: Write HANDOFF.md

Write to `{memory_directory}/HANDOFF.md`:

```markdown
<!-- Session Handoff — {YYYY-MM-DD HH:MM} -->

## Context
[2-3 sentence goal + project background relevant to this work]

## Project Context
- [Tech stack, architecture, or structural insight learned during session]
- [Non-obvious project quirk or convention discovered]

## Session Timeline
1. [First thing done/tried — with outcome]
2. [Next step — with outcome]
3. [Dead end tried and why it was abandoned]
4. [Current approach and where it stands]

## Discoveries
- [Surprising finding about the project]
- [Undocumented behavior or gotcha]

## Key Files
- `path/to/file.ext` - [role/status]

## Current State
[Exact resume point — what was just done, what's next]

## Open Items
- [ ] [Next immediate action]
- [ ] [Subsequent action]

## Constraints/Decisions
- [Decision and why it was made]
```

Sections with no content can be omitted. But don't omit a section just to save tokens — only if there's genuinely nothing to say.

### Step 5: Triage to CLAUDE.md (only with `--learn`)

If the user enabled learn, review the session for insights that are **stable project knowledge** — things that will be true next week, not just next session:

- Architecture decisions and rationale
- Project conventions and patterns
- Environment setup quirks
- Non-obvious dependencies or requirements
- "Always do X because Y" learnings

Present these as a suggested addition to CLAUDE.md:

```
I found these insights that might belong in CLAUDE.md (persistent project knowledge):

- [Insight 1]
- [Insight 2]

Should I append these to CLAUDE.md?
```

Only append after user confirmation. Format as concise bullet points that fit the existing CLAUDE.md style.

### Step 6: Confirm to User

After writing the file:

1. **Display** the handoff content in a fenced code block
2. **Copy to clipboard** using a platform-detecting fallback chain:
   ```bash
   cat "{memory_directory}/HANDOFF.md" | (pbcopy 2>/dev/null || xclip -selection clipboard 2>/dev/null || wl-copy 2>/dev/null || true)
   ```
   This tries macOS (`pbcopy`), Linux X11 (`xclip`), Linux Wayland (`wl-copy`) in order. If none are available, it silently succeeds — the file is saved either way.
3. **Confirm** in the user's language, e.g.: "Session saved to `memory/HANDOFF.md` and copied to clipboard."

---

## Mode: RESUME

### Step 1: Load Context

1. Read `{memory_directory}/HANDOFF.md`
2. Read `{memory_directory}/MEMORY.md` for background project context (if it exists)
3. If no HANDOFF.md exists, tell the user and start fresh

MEMORY.md provides stable project knowledge (managed by auto-memory). HANDOFF.md provides the specific resume point. Use both together — MEMORY.md for "what is this project" and HANDOFF.md for "where exactly did we stop."

### Step 2: Show Summary

Present a concise overview in the user's language. Include all sections that were saved — don't compress away the project context, timeline, or discoveries, as these are what make the resume valuable:

```
## Last Session

**Goal:** [from Context section]
**Status:** [from Current State section]

### Project Context
- [Tech stack, architecture insights]

### Session Timeline
1. [What happened in order, including dead ends]

### Discoveries
- [Surprising findings, gotchas]

### Key Files
- `path` - [role]

### Open Items
- [ ] [Remaining tasks]

### Constraints/Decisions
- [Decision and rationale]
```

Omit sections that are empty in the handoff, but don't omit sections just to keep it short.

### Step 3: Ask What To Continue With

Ask the user what they'd like to work on. If there are distinct open items, use AskUserQuestion to let them pick. Otherwise ask as free text.

### Step 4: Archive

Rename the handoff file so it doesn't trigger resume offers in future sessions:

```bash
mv "{memory_directory}/HANDOFF.md" "{memory_directory}/HANDOFF-{YYYY-MM-DD}.md"
```

---

## Mode: HISTORY

Show a summary of past sessions from archived handoff files.

### Step 1: Find Archives

List all `HANDOFF-*.md` files in `{memory_directory}/`, sorted by date (newest first). Also check if a current `HANDOFF.md` exists (unarchived).

### Step 2: Display Timeline

For each archived handoff, read the `<!-- Session Handoff — ... -->` header and the `## Context` section. Present a compact timeline:

```
## Session History

| Date | Goal | Status |
|---|---|---|
| 2026-03-14 | OAuth2 login flow (Google + GitHub) | GitHub callback 401 |
| 2026-03-12 | Set up CI/CD pipeline | Completed |
| 2026-03-10 | Initial project scaffolding | Completed |
```

If the user wants details on a specific session, read that archive file and show the full content.

### Step 3: Offer Cleanup

If there are more than 10 archived handoffs, suggest cleaning up old ones:

> "You have [N] archived handoffs. Want me to remove archives older than 30 days?"

Only delete after confirmation.

---

## Proactive Behavior

### At Session Start
If `{memory_directory}/HANDOFF.md` exists, offer to resume. Check the file's date (from the `<!-- Session Handoff — ... -->` header) and mention how old it is:

- **< 24h**: "I found a handoff from earlier today. Pick up where you left off?"
- **1-7 days**: "I found a handoff from [N days ago]. Want to resume?"
- **> 7 days**: "I found a handoff from [date], but it's [N days/weeks] old — it may be outdated. Want to review it, or start fresh?"

This is the single most valuable thing this skill does — it bridges the gap between sessions without requiring the user to remember what they were doing.

### During Long Sessions
When significant work has accumulated and the conversation is getting long, suggest saving a handoff. Context loss from a session ending without a save is the problem this skill exists to solve.

---

## Boundaries

- **MEMORY.md is read-only.** It's managed by the auto-memory system and contains stable project knowledge. This skill reads it but never writes to it.
- **CLAUDE.md** may only be modified when `--learn` is enabled and the user confirms the suggested additions.
- **HANDOFF.md is ephemeral.** It represents a single session transition — rich in detail, but not permanent. Stable learnings that should persist across all sessions belong in CLAUDE.md (via `--learn`) or MEMORY.md (managed separately).
- Use the project's auto-memory directory path for file operations.

---

## Example

**Save output** (`HANDOFF.md`):

```markdown
<!-- Session Handoff — 2026-02-26 15:30 -->

## Context
Adding OAuth2 login flow to the FastAPI backend (Google + GitHub providers).
The app is a SaaS dashboard with existing JWT auth — OAuth is an additional login method, not a replacement.

## Project Context
- FastAPI backend in `src/`, Alembic for migrations, PostgreSQL
- Auth middleware in `src/middleware/auth.py` — checks JWT on every request
- Frontend is React (Vite) in `frontend/`, uses `react-router` v6
- Tests use `pytest` + `httpx.AsyncClient`, need `TEST_DATABASE_URL` env var

## Session Timeline
1. Evaluated authlib vs requests-oauthlib — chose authlib (better async, less boilerplate)
2. Added Google OAuth: routes, callback, token exchange — working end to end
3. Extended User model with `provider` + `provider_id` fields, wrote Alembic migration
4. Tried adding GitHub OAuth using same pattern as Google
5. GitHub callback returns 401 — debugged for ~20 min, likely a scope issue in the GitHub app config (not a code problem)

## Discoveries
- `src/middleware/auth.py` silently swallows auth errors and returns 401 without logging — made debugging GitHub OAuth harder. Consider adding debug logging.
- Alembic `env.py` was configured for sync only — had to patch it for async. Fix is in `alembic/env.py:42-58`.

## Key Files
- `src/auth/oauth.py` - OAuth route handlers (Google working, GitHub WIP)
- `src/models/user.py` - User model with provider fields
- `alembic/versions/a3f8...py` - Migration for provider columns
- `.env.example` - Updated with GITHUB_CLIENT_ID/SECRET placeholders
- `src/middleware/auth.py` - Auth middleware (no changes, but relevant for debugging)

## Current State
Google OAuth complete and tested manually. GitHub OAuth callback returns 401 —
most likely the GitHub OAuth App needs `read:user` scope added (currently only has `user:email`).
Next step: check GitHub app settings, not code.

## Open Items
- [ ] Fix GitHub callback 401 — check scopes in GitHub app settings (Settings > Developer > OAuth Apps)
- [ ] Add logout endpoint that revokes OAuth tokens (authlib has `revoke_token()`)
- [ ] Write tests for both OAuth flows (mock external OAuth with `respx`)
- [ ] Consider adding debug logging to auth middleware

## Constraints/Decisions
- Using authlib over requests-oauthlib — better async support, less boilerplate
- Storing provider tokens encrypted via `cryptography.fernet`, key in env var
- OAuth is additive — existing JWT login stays, users can link OAuth later
```

**Resume output** (shown to user):

```
## Last Session (2026-02-26)

**Goal:** OAuth2 login (Google + GitHub) for FastAPI SaaS backend
**Status:** Google complete, GitHub callback 401 (likely scope config issue)

### Project Context
- FastAPI + Alembic + PostgreSQL, React frontend (Vite)
- Existing JWT auth in `src/middleware/auth.py`
- Tests: pytest + httpx.AsyncClient, needs TEST_DATABASE_URL

### Session Timeline
1. Chose authlib for OAuth (async support)
2. Google OAuth — working end to end
3. User model + migration for provider fields
4. GitHub OAuth — callback returns 401, likely scope issue (not code)

### Discoveries
- Auth middleware swallows errors silently — makes debugging hard
- Alembic env.py needed async patch (fix in `alembic/env.py:42-58`)

### Key Files
- `src/auth/oauth.py` - OAuth handlers (Google working, GitHub WIP)
- `src/models/user.py` - User model with provider fields
- `src/middleware/auth.py` - Auth middleware (relevant for debugging)

### Open Items
- [ ] Fix GitHub 401 (check app scopes, not code)
- [ ] Logout endpoint with token revocation
- [ ] Tests with respx mocking
- [ ] Debug logging for auth middleware

### Constraints/Decisions
- authlib over requests-oauthlib (async support)
- Provider tokens encrypted via cryptography.fernet
- OAuth is additive — JWT login stays

What should I continue with?
```
