---
name: session
description: >
  Session continuity with file-based handoff — saves and restores context across Claude Code sessions.
  Use this skill whenever the user wants to save, store, persist, or hand off their current session state,
  or when they want to resume, continue, restore, or pick up where they left off.
  Trigger words: "handoff", "save session", "speichern", "save", "continue later", "resume",
  "weitermachen", "load", "fortsetzen", "pick up", "where did we leave off", "last session".
  Also trigger PROACTIVELY: (1) at session start if memory/HANDOFF.md exists — offer to resume,
  (2) when context window is getting large — suggest saving before information is lost.
  Even if the user doesn't explicitly mention "session" or "handoff", trigger this skill whenever
  they clearly want to preserve work for later or restore previous work.
---

# Session Handoff

Preserve session context across conversation boundaries so the next session can pick up exactly where this one left off.

The core idea: a session produces knowledge that's expensive to rebuild — file paths discovered, decisions made, bugs diagnosed, approaches tried and rejected. HANDOFF.md captures this perishable context in a compact format that lets the next session skip the rediscovery phase entirely.

## Mode Detection

Determine mode from user input:
- **save**: "handoff", "save", "speichern", "continue later", "save session", or context is running low
- **resume**: "resume", "load", "weitermachen", "fortsetzen", "pick up", "where did we leave off", "last session"
- **auto-detect**: If `{memory_directory}/HANDOFF.md` exists and no explicit mode given, offer resume

If ambiguous, ask the user.

---

## Mode: SAVE

### Step 1: Analyze the Session

Review the conversation and identify what would be most expensive for a fresh session to rediscover:

- **Goal**: What's the user trying to accomplish?
- **Progress**: What's done and working?
- **Current state**: The exact point to resume from — what was just tried, what's next
- **Key artifacts**: Files modified, important paths, commands that worked
- **Blockers**: Unresolved issues, pending decisions
- **Context**: Domain knowledge, constraints, or preferences established during this session

### Step 2: Compress Intelligently

The goal is information density. A fresh Claude session already knows general programming concepts, standard library APIs, and common patterns — don't repeat those. Focus on what's unique to *this* session:

**High value** (include): specific file paths, function names, error messages, decisions with rationale, current hypothesis, reproduction steps, relevant IDs/URLs

**Low value** (omit): general knowledge, verbose explanations of standard concepts, full file contents (use path + line numbers), conversation meta-discussion

**Format**: bullet points over prose, paths over content, key error lines over full traces, "established: X" for agreed-upon decisions

### Step 3: Size to Complexity

Match handoff length to task complexity — a simple bug fix needs 100-200 tokens, a feature implementation 200-400, a multi-system architecture change 400-800. Don't pad simple tasks or truncate complex ones.

### Step 4: Write HANDOFF.md

Write to `{memory_directory}/HANDOFF.md`:

```markdown
<!-- Session Handoff — {YYYY-MM-DD HH:MM} -->

## Context
[1-2 sentence goal statement]

## Progress
- [Completed item with outcome]

## Current State
[Exact resume point — what was just done, what's next]

## Key Files
- `path/to/file.ext` - [role/status]

## Open Items
- [ ] [Next immediate action]
- [ ] [Subsequent action]

## Constraints/Decisions
- [Decision and why it was made]
```

### Step 5: Confirm to User

After writing the file:

1. **Display** the handoff content in a fenced code block
2. **Copy to clipboard** (detect platform):
   ```bash
   # macOS
   cat "{memory_directory}/HANDOFF.md" | pbcopy
   # Linux (X11)
   cat "{memory_directory}/HANDOFF.md" | xclip -selection clipboard
   # Linux (Wayland)
   cat "{memory_directory}/HANDOFF.md" | wl-copy
   ```
   If clipboard tools aren't available, skip silently — the file is saved either way.
3. **Confirm** in the user's language, e.g.: "Session saved to `memory/HANDOFF.md` and copied to clipboard."

---

## Mode: RESUME

### Step 1: Load Context

1. Read `{memory_directory}/HANDOFF.md`
2. Read `{memory_directory}/MEMORY.md` for background project context (if it exists)
3. If no HANDOFF.md exists, tell the user and start fresh

MEMORY.md provides stable project knowledge (managed by auto-memory). HANDOFF.md provides the specific resume point. Use both together — MEMORY.md for "what is this project" and HANDOFF.md for "where exactly did we stop."

### Step 2: Show Summary

Present a concise overview in the user's language:

```
## Last Session

**Goal:** [from Context section]
**Status:** [from Current State section]

### Completed
- [Progress items]

### Open Items
- [ ] [Remaining tasks]

### Key Files
- `path` - [role]
```

### Step 3: Ask What To Continue With

Ask the user what they'd like to work on. If there are distinct open items, use AskUserQuestion to let them pick. Otherwise ask as free text.

### Step 4: Archive

Rename the handoff file so it doesn't trigger resume offers in future sessions:

```bash
mv "{memory_directory}/HANDOFF.md" "{memory_directory}/HANDOFF-{YYYY-MM-DD}.md"
```

---

## Proactive Behavior

### At Session Start
If `{memory_directory}/HANDOFF.md` exists, offer to resume. This is the single most valuable thing this skill does — it bridges the gap between sessions without requiring the user to remember what they were doing.

### During Long Sessions
When significant work has accumulated and the conversation is getting long, suggest saving a handoff. Context loss from a session ending without a save is the problem this skill exists to solve.

---

## Boundaries

- **MEMORY.md is read-only.** It's managed by the auto-memory system and contains stable project knowledge. This skill reads it but never writes to it.
- **HANDOFF.md is ephemeral.** It represents a single session transition. Long-term learnings belong in MEMORY.md (managed separately), not here.
- Use the project's auto-memory directory path for all file operations.

---

## Example

**Save output** (`HANDOFF.md`):

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

**Resume output** (shown to user):

```
## Last Session

**Goal:** Adding OAuth2 login flow (Google + GitHub) to FastAPI backend
**Status:** Google flow complete, GitHub callback returns 401

### Completed
- Google OAuth2 working (login, callback, token exchange)
- User model extended with provider fields
- Alembic migration created and applied
- Frontend redirect working

### Open Items
- [ ] Debug GitHub callback 401 (check scopes)
- [ ] Add logout endpoint that revokes OAuth tokens
- [ ] Write tests for both OAuth flows

What should I continue with?
```
