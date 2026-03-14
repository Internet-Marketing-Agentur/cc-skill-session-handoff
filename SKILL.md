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

The core idea: a session produces two kinds of knowledge — **ephemeral state** (what's in progress right now) and **persistent insights** (what we learned about the project). HANDOFF.md captures the ephemeral state so the next session can resume. Persistent insights like project architecture, conventions, and discoveries belong in CLAUDE.md where they're available in every session automatically. The `--learn` option helps bridge the two.

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

Review the entire conversation — not just the last few exchanges. Also run `git diff --stat` and `git status` to capture file changes that may not have been explicitly discussed.

Focus on **session state** — what's needed to resume work:

- **Goal**: What's the user trying to accomplish?
- **Current state**: The exact point to resume from — what was just tried, what's next
- **Key artifacts**: Combine files mentioned in conversation with `git diff --stat` output. This catches files that were edited but never explicitly discussed.
- **Blockers**: Unresolved issues, pending decisions
- **Decisions**: Choices made during the session and why

Don't capture project architecture, tech stack, conventions, or discoveries here — those belong in CLAUDE.md (use `--learn` to extract them).

### Step 2: Compress Intelligently

The goal is information density — but err on the side of including too much rather than too little. A handoff that's too brief forces the next session to rediscover context, which is the exact problem this skill exists to solve.

A fresh Claude session already knows general programming concepts, standard library APIs, and common patterns — don't repeat those. Focus on what's unique to *this project* and *this session*:

**High value** (include): file paths, function names, error messages, decisions with rationale, dead ends and why they failed, current hypothesis, reproduction steps, relevant IDs/URLs

**Low value** (omit): general programming knowledge, project architecture (belongs in CLAUDE.md), verbose explanations of standard concepts, full file contents (use path + line numbers), conversation meta-discussion

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
[1-2 sentence goal statement]

## Current State
[Exact resume point — what was just done, what's next]

## Key Files
- `path/to/file.ext` - [role/status/what changed]

## Open Items
- [ ] [Next immediate action]
- [ ] [Subsequent action]

## Dead Ends
- [Approach tried and why it was abandoned]

## Decisions
- [Decision and why it was made]
```

Keep a "Dead Ends" section when approaches were tried and abandoned — this prevents the next session from repeating them. Omit it if there were no dead ends.

### Step 5: Extract learnings (only with `--learn`)

If the user enabled learn, review the session for **stable project knowledge** — things that will be true next week, not just next session. Route them to the right file:

**→ DECISIONS.md** (appended automatically, no confirmation needed):
- Technical or architectural decisions made during the session
- Each entry with date, decision, rationale, and alternatives considered
- Format per `DECISIONS.md.template` bundled with this skill
- If no `DECISIONS.md` exists yet, create one from the template

**→ CLAUDE.md** (only after user confirmation):
- **Architecture**: component relationships, structural insights
- **Conventions**: patterns, naming, workflow rules established
- **Environment & Setup**: setup quirks, test prerequisites, required tooling
- **Discoveries & Gotchas**: undocumented behavior, surprising dependencies
- If no `CLAUDE.md` exists, suggest creating one from `CLAUDE.md.template`

Present the split clearly:

```
Logged to DECISIONS.md:

### 2026-02-26 — OAuth library choice
**Decision:** authlib over requests-oauthlib
**Rationale:** Better async support, less boilerplate
**Alternatives considered:** requests-oauthlib (no native async)

---

These insights could go into CLAUDE.md:

**Discoveries & Gotchas**
- Auth middleware in `src/middleware/auth.py` swallows errors silently

**Environment & Setup**
- Alembic env.py needs async patch (fix in `alembic/env.py:42-58`)
- Tests require `TEST_DATABASE_URL` env var

Should I add these to CLAUDE.md?
```

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

Present a concise overview in the user's language. Mirror the sections from the handoff:

```
## Last Session ({date})

**Goal:** [from Context]
**Status:** [from Current State]

### Key Files
- `path` - [role]

### Open Items
- [ ] [Remaining tasks]

### Dead Ends
- [What was tried and why it didn't work]

### Decisions
- [Key decisions from this session]
```

Omit sections that are empty in the handoff.

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
- **DECISIONS.md** is appended automatically when `--learn` is enabled — no confirmation needed for decisions, since the CLAUDE.md rule already authorizes this.
- **HANDOFF.md is ephemeral.** It represents a single session transition. Stable knowledge belongs in CLAUDE.md, decisions in DECISIONS.md.
- Use the project's auto-memory directory path for file operations.

---

## Example

**Save output** (`HANDOFF.md`):

```markdown
<!-- Session Handoff — 2026-02-26 15:30 -->

## Context
Adding OAuth2 login flow (Google + GitHub) to FastAPI SaaS backend.

## Current State
Google OAuth complete and tested manually. GitHub OAuth callback returns 401 —
most likely the GitHub OAuth App needs `read:user` scope added (currently only has `user:email`).
Next step: check GitHub app settings, not code.

## Key Files
- `src/auth/oauth.py` - OAuth route handlers (Google working, GitHub WIP)
- `src/models/user.py` - User model with `provider` + `provider_id` fields
- `alembic/versions/a3f8...py` - Migration for provider columns
- `.env.example` - Updated with GITHUB_CLIENT_ID/SECRET placeholders

## Open Items
- [ ] Fix GitHub callback 401 — check scopes in GitHub app settings
- [ ] Add logout endpoint (authlib has `revoke_token()`)
- [ ] Write tests for both OAuth flows (mock with `respx`)

## Dead Ends
- Tried debugging GitHub 401 as a code issue for ~20 min — it's a config issue (scope missing in GitHub app settings)

## Decisions
- authlib over requests-oauthlib — better async support, less boilerplate
- Provider tokens encrypted via `cryptography.fernet`, key in env var
- OAuth is additive — existing JWT login stays
```

**`--learn` output** (decisions logged, CLAUDE.md suggestions):

```
Logged to DECISIONS.md:

### 2026-02-26 — OAuth library choice
**Decision:** authlib over requests-oauthlib
**Rationale:** Better async support, less boilerplate
**Alternatives considered:** requests-oauthlib (no native async)

### 2026-02-26 — Token storage strategy
**Decision:** Encrypt provider tokens via cryptography.fernet
**Rationale:** Tokens are sensitive credentials, plain text unacceptable
**Alternatives considered:** Plain text (rejected), vault integration (overkill for now)

---

These insights could go into CLAUDE.md:

**Discoveries & Gotchas**
- Auth middleware in `src/middleware/auth.py` swallows errors silently

**Environment & Setup**
- Alembic env.py needs async patch (fix in `alembic/env.py:42-58`)
- Tests require `TEST_DATABASE_URL` env var

Should I add these to CLAUDE.md?
```

**Resume output** (shown to user):

```
## Last Session (2026-02-26)

**Goal:** OAuth2 login (Google + GitHub) for FastAPI backend
**Status:** Google complete, GitHub callback 401 (scope config issue)

### Key Files
- `src/auth/oauth.py` - OAuth handlers (Google working, GitHub WIP)
- `src/models/user.py` - User model with provider fields

### Open Items
- [ ] Fix GitHub 401 (check app scopes, not code)
- [ ] Logout endpoint with token revocation
- [ ] Tests with respx mocking

### Dead Ends
- GitHub 401 is not a code issue — scope missing in GitHub app config

What should I continue with?
```
