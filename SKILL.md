---
name: session
description: >
  Session continuity with file-based handoff — saves and restores context across Claude Code sessions.
  Use this skill whenever the user wants to save, store, persist, or hand off their current session state,
  or when they want to resume, continue, restore, or pick up where they left off.
  Trigger phrases (must indicate session/context, not a file-save): "handoff", "save session",
  "save context", "save our progress", "session speichern", "sitzung speichern", "continue later",
  "resume", "resume session", "weitermachen", "load session", "fortsetzen", "pick up where we left off",
  "where did we leave off", "last session", "session history", "past sessions".
  Do NOT trigger on bare "save"/"speichern" when it clearly refers to a file or code ("save this file",
  "save the config", "speicher die Datei").
  Also trigger PROACTIVELY: (1) at session start if memory/HANDOFF.md exists — offer to resume,
  (2) when context window is getting large — suggest saving before information is lost.
  Even if the user doesn't explicitly mention "session" or "handoff", trigger this skill whenever
  they clearly want to preserve work for later or restore previous work.
---

# Session Handoff

Preserve session context across conversation boundaries so the next session can pick up exactly where this one left off.

The core idea: a session produces two kinds of knowledge — **ephemeral state** (what's in progress right now) and **persistent insights** (what we learned about the project). HANDOFF.md captures the ephemeral state so the next session can resume. Persistent insights like project architecture, conventions, and discoveries belong in CLAUDE.md where they're available in every session automatically. The `--learn` option helps bridge the two.

## File Locations

This skill works with four kinds of files. Each has a defined location:

| File | Location | Owner | Notes |
|---|---|---|---|
| `HANDOFF.md` (+ archives) | `{memory_directory}` (see resolver below) | this skill | Ephemeral, session-bound, **must be gitignored** |
| `MEMORY.md` | `~/.claude/projects/<cwd-slug>/memory/MEMORY.md` (auto-memory default) | auto-memory system | Read-only for this skill |
| `DECISIONS.md` | **project root** (`<project-root>/DECISIONS.md`) | this skill (via `--learn`) | Persistent architectural log, committed to repo |
| `CLAUDE.md` | **project root** (`<project-root>/CLAUDE.md`) | user (suggested by `--learn`) | Persistent project knowledge, committed to repo |

### Resolving `{memory_directory}` (for HANDOFF.md only)

In order, stopping at the first that applies:

1. An explicit path the user provides in the current request (e.g. "save to `docs/sessions/`")
2. `$CLAUDE_MEMORY_DIR` if set in the environment
3. `<project-root>/.claude/memory/` (project root = git top-level, or CWD if not a git repo)

Project-local storage is the default because it travels with the project when the directory is moved or copied. Always write HANDOFF files to this same directory so save and resume stay consistent. Create the directory if it does not exist.

### Resolving `MEMORY.md`

Look in this order, returning the first found (do not merge):

1. `{memory_directory}/MEMORY.md` (project-local, if user moved it there manually)
2. `~/.claude/projects/<cwd-slug>/memory/MEMORY.md` (auto-memory default)

The slug is derived from the absolute CWD path: replace `/` with `-`, drop the leading `-`. Example: `/Users/achim/Documents/Code/hr` → `-Users-achim-Documents-Code-hr`.

### Fallback for legacy HANDOFF / DECISIONS files

Older sessions may have stored these files under `~/.claude/projects/<cwd-slug>/memory/`. When opening a project for the first time after this skill update:

- **HANDOFF.md fallback (RESUME mode)**: If no HANDOFF.md is in `{memory_directory}` but one exists at `~/.claude/projects/<cwd-slug>/memory/HANDOFF.md`, ask the user: *"Found a legacy handoff at the old location. Migrate it into the project folder and resume?"* On confirm, `mv` the file and proceed. On decline, read in place but do not archive it.
- **DECISIONS.md fallback (`--learn` mode)**: If no `<project-root>/DECISIONS.md` exists but one is found at `~/.claude/projects/<cwd-slug>/memory/DECISIONS.md`, ask: *"Found legacy DECISIONS.md — move it into the project root?"* On confirm, `mv` it. On decline, append to the legacy location for now.

### Gitignore hygiene

When `{memory_directory}` is inside a git repo (check with `git rev-parse --is-inside-work-tree`), ensure `.claude/memory/` is ignored:

1. If no `.gitignore` exists, create one with the line `.claude/memory/`.
2. If `.gitignore` exists but does not already match `.claude/memory/` or `.claude/memory/HANDOFF*.md`, append `.claude/memory/` and inform the user.
3. If it already matches, stay silent.

Reason: handoffs can contain error messages with tokens, internal paths, or sensitive context that should not be committed. `DECISIONS.md` and `CLAUDE.md` are the opposite — they belong in the repo, so do not gitignore them.

## Helper Script

All deterministic operations (path resolution, existence checks, header parsing, archive renaming, gitignore hygiene, legacy file migration, archive listing) are delegated to a single Python helper. This collapses what would be 5–8 separate Bash calls per save into 1–2 calls and emits structured JSON for the skill to consume.

**Path:**
```
${SESSION_HELPER:-$HOME/.claude/skills/session/scripts/session_helper.py}
```

Set `SESSION_HELPER` in the environment if the skill is installed under a non-default location (e.g. as a plugin under `~/.claude/plugins/`).

**Subcommands** (all output JSON to stdout):

| Command | Purpose |
|---|---|
| `paths --cwd <cwd>` | One-shot resolver: project root, slug, memory dirs, gitignore status, plus existence + header date + first context line for HANDOFF/MEMORY/DECISIONS/CLAUDE in both primary and legacy locations. Use this **once** at the start of every mode. |
| `archive --memory-dir <dir>` | Rename `HANDOFF.md` → `HANDOFF-YYYY-MM-DD-HHMM.md` (numeric suffix on collision). |
| `gitignore --root <dir>` | Ensure `.claude/memory/` is in `.gitignore`. Creates `.gitignore` if missing. No-op outside git repos. |
| `migrate --src <legacy_path> --dst <new_path>` | Move a legacy file safely (refuses if target exists). |
| `list --memory-dir <dir> --legacy-dir <dir>` | List all `HANDOFF*.md` archives in both locations with header date, context, source tag, age in days. |

**Standard preamble for every mode** — run this first, then read the JSON to decide what to do:

```bash
HELPER="${SESSION_HELPER:-$HOME/.claude/skills/session/scripts/session_helper.py}"
python3 "$HELPER" paths --cwd "$PWD"
```

## Parameters

The `learn` parameter controls whether the save process tries to extract stable project knowledge into `DECISIONS.md` and `CLAUDE.md`. Three settings:

| Mode | When to use | Behavior |
|---|---|---|
| `--learn` | User explicitly asks for it (CLI flag or natural-language trigger) | Force extraction even if heuristics find no obvious candidates. |
| `--no-learn` | User explicitly suppresses it | Skip extraction entirely. HANDOFF.md only. |
| **default** (auto-detect) | No explicit flag | Scan the session for candidates. If found, **ask once** whether to log them. If not found, stay silent. |

**Auto-detect heuristics** — look for any of:

- Decision markers: *"decided to", "we'll use X over Y", "going with", "chose", "rejected", "abandoned in favor of"*
- Discovery markers: *"turns out", "it's because", "gotcha", "watch out for", "actually", "the real reason"*
- Convention markers: *"from now on", "convention is", "always do X", "never do Y", "rule:"*
- Setup-quirk markers: *"need to", "first run", "prerequisite", "must have", "won't work without"*

If at least one candidate is detected, prompt:

> *"This session contains [N] possible DECISIONS entries and [M] CLAUDE.md insights. Should I log them?"*

The user answers yes/no. Treat *yes* as if `--learn` had been set; treat *no* as `--no-learn`.

**Natural-language triggers for explicit `--learn`:**
*"with learn", "with learnings", "save learnings", "save with lessons learned", "mit lernen", "und merke dir", "speichere mit lessons learned", "speicher Erkenntnisse"*.

**Natural-language triggers for explicit `--no-learn`:**
*"no learn", "skip learnings", "ohne lernen", "nur handoff"*.

## Mode Detection

Determine mode from user input:
- **save**: "handoff", "save session", "save context", "session speichern", "continue later", or context is running low
- **resume**: "resume", "resume session", "load session", "weitermachen", "fortsetzen", "pick up where we left off", "where did we leave off", "last session"
- **history**: "session history", "past sessions", "session log", `/session history`
- **auto-detect**: If `{memory_directory}/HANDOFF.md` exists and no explicit mode given, offer resume

Bare "save" / "speichern" without session context almost always refers to a file — do **not** trigger save mode in that case. Ask the user to confirm before activating the skill if intent is ambiguous.

## Language

All user-facing output (summaries, confirmations, questions) must match the language of the user's most recent message. Detect it explicitly before writing anything back: if the triggering message is in German, respond in German; if English, English; otherwise match whatever language the user used. The **file contents** of HANDOFF.md itself stay in English for consistency across tools and future sessions — only the conversational wrapper adapts.

---

## Mode: SAVE

### Step 1: Analyze the Session

First, run the helper preamble (see Helper Script section) to resolve all paths and existence flags in one call. Then review the entire conversation — not just the last few exchanges. Also run `git diff --stat` and `git status` to capture file changes that may not have been explicitly discussed.

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

### Step 5: Extract learnings (when learn is active)

`learn` is active if (a) the user passed `--learn` explicitly, or (b) the user passed nothing and the auto-detect heuristics (see Parameters section) found at least one candidate AND the user confirmed when prompted. If `learn` is not active, skip this step entirely.

Review the session for **stable project knowledge** — things that will be true next week, not just next session. Route them to the right file:

**→ DECISIONS.md** (target: `<project-root>/DECISIONS.md`, appended automatically, no confirmation needed — entries are additive and easily reverted):
- Technical or architectural decisions made during the session
- Each entry with date, decision, rationale, and alternatives considered
- Format per `DECISIONS.md.template` bundled with this skill
- If no `<project-root>/DECISIONS.md` exists, apply the **DECISIONS.md fallback** (see File Locations) before creating a new one from the template

**→ CLAUDE.md** (target: `<project-root>/CLAUDE.md`, only after user confirmation):
- **Architecture**: component relationships, structural insights
- **Conventions**: patterns, naming, workflow rules established
- **Environment & Setup**: setup quirks, test prerequisites, required tooling
- **Discoveries & Gotchas**: undocumented behavior, surprising dependencies
- If no `<project-root>/CLAUDE.md` exists, suggest creating one from `CLAUDE.md.template`

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

### Step 6: Ensure Gitignore & Confirm to User

After writing the file:

1. **Ensure `.gitignore` is up to date** (only when inside a git repo — the helper handles the no-op case):
   ```bash
   python3 "$HELPER" gitignore --root "<project-root>"
   ```
   If the action returned is `created` or `appended`, mention it in the confirmation. If `already_present` or `not_a_repo`, stay silent.
2. **Display** the handoff content in a fenced code block
3. **Copy to clipboard** using a platform-detecting fallback chain:
   ```bash
   cat "{memory_directory}/HANDOFF.md" | (pbcopy 2>/dev/null || xclip -selection clipboard 2>/dev/null || wl-copy 2>/dev/null || true)
   ```
   This tries macOS (`pbcopy`), Linux X11 (`xclip`), Linux Wayland (`wl-copy`) in order. If none are available, it silently succeeds — the file is saved either way.
4. **Confirm** in the user's language, e.g.: "Session saved to `.claude/memory/HANDOFF.md` and copied to clipboard."

---

## Mode: RESUME

### Step 1: Load Context

1. Run the helper preamble (`paths --cwd "$PWD"`) to resolve all locations and existence flags in one call.
2. Read `HANDOFF.md` using the JSON output: prefer `handoff.current` if `current_exists` is true; otherwise apply the **HANDOFF.md fallback** if `handoff.legacy_exists` is true — offer migration via `python3 "$HELPER" migrate --src <legacy> --dst <current>` after user confirmation.
3. Read `MEMORY.md` using `memory_md.resolved` from the helper output (already resolved against both primary and legacy paths).
4. If no HANDOFF.md is found in either location, tell the user and start fresh.

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

Rename the handoff file so it doesn't trigger resume offers in future sessions. The helper handles timestamp generation and conflict suffixes:

```bash
python3 "$HELPER" archive --memory-dir "<memory_dir>"
```

The JSON response includes `to`, the new archive path. Use it in the confirmation message.

---

## Mode: HISTORY

Show a summary of past sessions from archived handoff files.

### Step 1: Find Archives

Use the helper:

```bash
python3 "$HELPER" list --memory-dir "<memory_dir>" --legacy-dir "<legacy_memory_dir>"
```

It returns a sorted JSON list of all `HANDOFF*.md` files (current + archives) from both locations, each tagged with `source` (`local` or `legacy`), plus header date, first context line, and age in days.

### Step 2: Display Timeline

For each archive, read the `<!-- Session Handoff — ... -->` header and the `## Context` section. Annotate the source so the user can see which entries live in the legacy location:

```
## Session History

| Date | Goal | Status | Source |
|---|---|---|---|
| 2026-03-14 | OAuth2 login flow (Google + GitHub) | GitHub callback 401 | local |
| 2026-03-12 | Set up CI/CD pipeline | Completed | local |
| 2026-03-10 | Initial project scaffolding | Completed | legacy |
```

If the user wants details on a specific session, read that archive file and show the full content.

### Step 3: Offer Migration & Cleanup

- If any entries are tagged `legacy`, offer once: *"Move all [N] legacy archives into the project folder?"* On confirm, `mv` them.
- If there are more than 10 archived handoffs (combined), suggest cleaning up old ones: *"You have [N] archived handoffs. Want me to remove archives older than 30 days?"*

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

- **MEMORY.md is read-only.** It's managed by the auto-memory system and lives at `~/.claude/projects/<cwd-slug>/memory/` by default. This skill reads it but never writes to it.
- **CLAUDE.md** lives in the project root and may only be modified when `--learn` is enabled and the user confirms the suggested additions.
- **DECISIONS.md** lives in the project root. It is appended automatically when `--learn` is enabled — no confirmation needed because entries are factual, chronological, and additive (a bad entry is trivially reverted by deleting one block).
- **HANDOFF.md is ephemeral.** It represents a single session transition, lives in `<project-root>/.claude/memory/`, and must be gitignored. Stable knowledge belongs in CLAUDE.md, decisions in DECISIONS.md.
- See **File Locations** at the top of this document for the full resolver and fallback rules.

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
