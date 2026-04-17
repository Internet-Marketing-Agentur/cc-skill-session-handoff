#!/usr/bin/env python3
"""
session_helper — deterministic helpers for the session skill.

All commands print a single JSON object to stdout. Use --cwd to override
the working directory (defaults to $PWD). No third-party dependencies.

Subcommands:
  paths      Resolve all paths, existence, git state, file headers (one-shot).
  archive    Rename HANDOFF.md to HANDOFF-{YYYY-MM-DD-HHMM}.md (with conflict suffix).
  gitignore  Ensure `.claude/memory/` is gitignored in the project root.
  migrate    Move a legacy file into its new location (with safety checks).
  list       List all HANDOFF archives across primary + legacy locations.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
HEADER_RE = re.compile(r"<!--\s*Session Handoff\s*[—-]\s*(.+?)\s*-->")
CONTEXT_RE = re.compile(r"^##\s*Context\s*$\n+(.+?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)


# ---------- core helpers ----------

def slug_from_cwd(cwd: str) -> str:
    """Mirror Claude Code's auto-memory slug: '/Users/x/y' -> '-Users-x-y'."""
    return cwd.replace("/", "-")


def project_root(cwd: str) -> str:
    """Return git top-level if inside a repo, else CWD."""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return cwd


def is_git_repo(cwd: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def parse_handoff_header(path: Path) -> tuple[str | None, str | None]:
    """Return (header_date, context_first_line) or (None, None) if unreadable."""
    if not path.is_file():
        return (None, None)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return (None, None)
    header = HEADER_RE.search(text)
    header_date = header.group(1).strip() if header else None
    ctx = CONTEXT_RE.search(text)
    context = None
    if ctx:
        # collapse to first non-empty line
        for line in ctx.group(1).splitlines():
            stripped = line.strip()
            if stripped:
                context = stripped
                break
    return (header_date, context)


def file_age_days(path: Path) -> float | None:
    if not path.is_file():
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    delta = datetime.now(tz=timezone.utc) - mtime
    return round(delta.total_seconds() / 86400, 2)


# ---------- subcommands ----------

def cmd_paths(args: argparse.Namespace) -> dict:
    cwd = args.cwd
    root = project_root(cwd)
    slug = slug_from_cwd(cwd)
    env_dir = os.environ.get("CLAUDE_MEMORY_DIR")

    if env_dir:
        memory_dir = Path(env_dir).expanduser().resolve()
    else:
        memory_dir = Path(root) / ".claude" / "memory"

    legacy_memory_dir = HOME / ".claude" / "projects" / slug / "memory"
    project_root_path = Path(root)

    # HANDOFF
    handoff_current = memory_dir / "HANDOFF.md"
    handoff_legacy = legacy_memory_dir / "HANDOFF.md"
    cur_date, cur_ctx = parse_handoff_header(handoff_current)
    leg_date, leg_ctx = parse_handoff_header(handoff_legacy)

    # MEMORY.md (read-only resolver)
    memory_primary = memory_dir / "MEMORY.md"
    memory_legacy = legacy_memory_dir / "MEMORY.md"
    if memory_primary.is_file():
        memory_resolved = str(memory_primary)
    elif memory_legacy.is_file():
        memory_resolved = str(memory_legacy)
    else:
        memory_resolved = None

    # DECISIONS.md
    decisions_primary = project_root_path / "DECISIONS.md"
    decisions_legacy = legacy_memory_dir / "DECISIONS.md"

    # CLAUDE.md
    claude_primary = project_root_path / "CLAUDE.md"

    # gitignore state
    gitignore = project_root_path / ".gitignore"
    memory_ignored = False
    if gitignore.is_file():
        try:
            lines = [l.strip() for l in gitignore.read_text(encoding="utf-8", errors="replace").splitlines()]
            memory_ignored = any(
                l in (".claude/memory/", ".claude/memory", ".claude/memory/HANDOFF*.md", ".claude/")
                for l in lines
            )
        except OSError:
            pass

    return {
        "cwd": cwd,
        "project_root": root,
        "slug": slug,
        "is_git_repo": is_git_repo(cwd),
        "memory_dir": str(memory_dir),
        "memory_dir_exists": memory_dir.is_dir(),
        "memory_dir_source": "env" if env_dir else "project",
        "legacy_memory_dir": str(legacy_memory_dir),
        "legacy_memory_dir_exists": legacy_memory_dir.is_dir(),
        "handoff": {
            "current": str(handoff_current),
            "current_exists": handoff_current.is_file(),
            "current_age_days": file_age_days(handoff_current),
            "current_header_date": cur_date,
            "current_context": cur_ctx,
            "legacy": str(handoff_legacy),
            "legacy_exists": handoff_legacy.is_file(),
            "legacy_age_days": file_age_days(handoff_legacy),
            "legacy_header_date": leg_date,
            "legacy_context": leg_ctx,
        },
        "memory_md": {
            "primary": str(memory_primary),
            "primary_exists": memory_primary.is_file(),
            "legacy": str(memory_legacy),
            "legacy_exists": memory_legacy.is_file(),
            "resolved": memory_resolved,
        },
        "decisions_md": {
            "primary": str(decisions_primary),
            "primary_exists": decisions_primary.is_file(),
            "legacy": str(decisions_legacy),
            "legacy_exists": decisions_legacy.is_file(),
        },
        "claude_md": {
            "primary": str(claude_primary),
            "primary_exists": claude_primary.is_file(),
        },
        "gitignore": {
            "path": str(gitignore),
            "exists": gitignore.is_file(),
            "memory_ignored": memory_ignored,
        },
    }


def cmd_archive(args: argparse.Namespace) -> dict:
    memory_dir = Path(args.memory_dir).expanduser().resolve()
    src = memory_dir / "HANDOFF.md"
    if not src.is_file():
        return {"action": "no_handoff", "memory_dir": str(memory_dir)}
    ts = datetime.now().strftime("%Y-%m-%d-%H%M")
    target = memory_dir / f"HANDOFF-{ts}.md"
    suffix = 2
    while target.exists():
        target = memory_dir / f"HANDOFF-{ts}-{suffix}.md"
        suffix += 1
    src.rename(target)
    return {"action": "archived", "from": str(src), "to": str(target)}


def cmd_gitignore(args: argparse.Namespace) -> dict:
    root = Path(args.root).expanduser().resolve()
    if not is_git_repo(str(root)):
        return {"action": "not_a_repo", "root": str(root)}
    gi = root / ".gitignore"
    line = ".claude/memory/"
    if not gi.is_file():
        gi.write_text(line + "\n", encoding="utf-8")
        return {"action": "created", "path": str(gi), "added": line}
    existing = gi.read_text(encoding="utf-8", errors="replace")
    matches = (".claude/memory/", ".claude/memory", ".claude/memory/HANDOFF*.md", ".claude/")
    for raw in existing.splitlines():
        if raw.strip() in matches:
            return {"action": "already_present", "path": str(gi), "matched": raw.strip()}
    sep = "" if existing.endswith("\n") or not existing else "\n"
    with gi.open("a", encoding="utf-8") as f:
        f.write(f"{sep}{line}\n")
    return {"action": "appended", "path": str(gi), "added": line}


def cmd_migrate(args: argparse.Namespace) -> dict:
    src = Path(args.src).expanduser().resolve()
    dst = Path(args.dst).expanduser().resolve()
    if not src.is_file():
        return {"action": "source_missing", "src": str(src)}
    if dst.exists():
        return {"action": "skipped_target_exists", "src": str(src), "dst": str(dst)}
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return {"action": "moved", "src": str(src), "dst": str(dst)}


def cmd_list(args: argparse.Namespace) -> dict:
    memory_dir = Path(args.memory_dir).expanduser().resolve()
    legacy_dir = Path(args.legacy_dir).expanduser().resolve() if args.legacy_dir else None

    entries = []

    def collect(directory: Path, source: str):
        if not directory.is_dir():
            return
        for path in sorted(directory.iterdir(), reverse=True):
            if not path.is_file() or not path.name.startswith("HANDOFF"):
                continue
            if not path.name.endswith(".md"):
                continue
            is_current = path.name == "HANDOFF.md"
            date, context = parse_handoff_header(path)
            entries.append({
                "path": str(path),
                "name": path.name,
                "source": source,
                "is_current": is_current,
                "header_date": date,
                "context": context,
                "age_days": file_age_days(path),
            })

    collect(memory_dir, "local")
    if legacy_dir and legacy_dir != memory_dir:
        collect(legacy_dir, "legacy")

    # Sort: current first within source, then by header_date desc (fallback name desc)
    def sort_key(e):
        return (
            0 if e["is_current"] else 1,
            -(datetime.strptime(e["header_date"][:16], "%Y-%m-%d %H:%M").timestamp())
            if e["header_date"] and re.match(r"\d{4}-\d{2}-\d{2}", e["header_date"][:10])
            else 0,
            e["name"],
        )
    try:
        entries.sort(key=sort_key)
    except Exception:
        entries.sort(key=lambda e: (0 if e["is_current"] else 1, e["name"]), reverse=False)

    return {"handoffs": entries, "count": len(entries)}


# ---------- main ----------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_paths = sub.add_parser("paths", help="Resolve paths and existence flags.")
    p_paths.add_argument("--cwd", default=os.getcwd())

    p_arch = sub.add_parser("archive", help="Archive HANDOFF.md with timestamp suffix.")
    p_arch.add_argument("--memory-dir", required=True)

    p_gi = sub.add_parser("gitignore", help="Ensure .claude/memory/ is gitignored.")
    p_gi.add_argument("--root", required=True)

    p_mig = sub.add_parser("migrate", help="Move a legacy file to its new location.")
    p_mig.add_argument("--src", required=True)
    p_mig.add_argument("--dst", required=True)

    p_list = sub.add_parser("list", help="List handoff archives across primary + legacy.")
    p_list.add_argument("--memory-dir", required=True)
    p_list.add_argument("--legacy-dir", default=None)

    args = parser.parse_args()

    handlers = {
        "paths": cmd_paths,
        "archive": cmd_archive,
        "gitignore": cmd_gitignore,
        "migrate": cmd_migrate,
        "list": cmd_list,
    }
    try:
        result = handlers[args.cmd](args)
    except Exception as exc:  # surface errors as JSON for consistency
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}), file=sys.stdout)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
