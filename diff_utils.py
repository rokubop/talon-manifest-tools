"""
Diff utilities for talon-pack generators.
Provides unified diff output for comparing old vs new content.
"""
import difflib
import json
import os

# ANSI color codes (no third-party deps)
# Check if colors should be disabled (NO_COLOR env var or dumb terminal)
_NO_COLOR = os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb"

RED = "" if _NO_COLOR else "\033[31m"
GREEN = "" if _NO_COLOR else "\033[32m"
YELLOW = "" if _NO_COLOR else "\033[33m"
CYAN = "" if _NO_COLOR else "\033[36m"
DIM = "" if _NO_COLOR else "\033[2m"
RESET = "" if _NO_COLOR else "\033[0m"


def colorize_diff(diff: str) -> str:
    """Add colors to unified diff output."""
    if _NO_COLOR:
        return diff
    lines = []
    for line in diff.splitlines():
        if line.startswith('+++') or line.startswith('---'):
            lines.append(f"{DIM}{line}{RESET}")
        elif line.startswith('+'):
            lines.append(f"{GREEN}{line}{RESET}")
        elif line.startswith('-'):
            lines.append(f"{RED}{line}{RESET}")
        elif line.startswith('@@'):
            lines.append(f"{CYAN}{line}{RESET}")
        else:
            lines.append(line)
    return "\n".join(lines)


def status_no_change(filename: str) -> str:
    """Format 'no changes' message."""
    return f"{DIM}{filename}: no changes{RESET}"


def status_created(filename: str) -> str:
    """Format 'created' message."""
    return f"{GREEN}{filename}: created{RESET}"


def status_warning(message: str) -> str:
    """Format warning message."""
    return f"{YELLOW}{message}{RESET}"


def status_error(message: str) -> str:
    """Format error message."""
    return f"{RED}{message}{RESET}"


def diff_json(old_content: str, new_content: str, filename: str = "file") -> tuple[bool, str]:
    """
    Compare two JSON strings and return a unified diff.

    Returns:
        (has_changes, diff_output) - tuple of whether there are changes and the diff string
    """
    if old_content == new_content:
        return False, ""

    # Parse and re-serialize to normalize formatting
    try:
        old_normalized = json.dumps(json.loads(old_content), indent=2, ensure_ascii=False)
        new_normalized = json.dumps(json.loads(new_content), indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        old_normalized = old_content
        new_normalized = new_content

    if old_normalized == new_normalized:
        return False, ""

    diff_lines = list(difflib.unified_diff(
        old_normalized.splitlines(keepends=True),
        new_normalized.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    ))

    return True, "".join(diff_lines)


def diff_text(old_content: str, new_content: str, filename: str = "file") -> tuple[bool, str]:
    """
    Compare two text strings and return a unified diff.

    Returns:
        (has_changes, diff_output) - tuple of whether there are changes and the diff string
    """
    if old_content == new_content:
        return False, ""

    diff_lines = list(difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    ))

    return True, "".join(diff_lines)


def format_diff_output(diff: str, max_lines: int = None) -> str:
    """
    Format diff output with colors, optionally truncating if too long.
    If max_lines is None, no truncation occurs.
    """
    colored = colorize_diff(diff)
    if max_lines is None:
        return colored
    lines = colored.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n{DIM}... ({len(lines) - max_lines} more lines){RESET}"
    return colored
