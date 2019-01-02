"""Readable JSON comparison with colorized terminal output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


__all__ = [
    "ChangeType",
    "Change",
    "diff",
    "format_diff",
    "diff_summary",
]


class ChangeType(Enum):
    """Type of change detected between two values."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class Change:
    """A single difference between two JSON-compatible objects."""

    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None


def diff(
    a: Any,
    b: Any,
    ignore: set[str] | list[str] | None = None,
    _path: str = "",
) -> list[Change]:
    """Compare two JSON-compatible objects and return a list of changes.

    Args:
        a: The original object.
        b: The new object.
        ignore: Set of top-level or dot-path keys to ignore.
        _path: Internal path prefix for recursion.

    Returns:
        List of Change objects describing every difference.
    """
    ignore_set = set(ignore) if ignore else set()
    return _diff_values(a, b, _path, ignore_set)


def _should_ignore(path: str, ignore: set[str]) -> bool:
    if not ignore:
        return False
    if path in ignore:
        return True
    parts = path.rsplit(".", 1)
    return parts[-1] in ignore if len(parts) > 1 else False


def _diff_values(
    a: Any, b: Any, path: str, ignore: set[str]
) -> list[Change]:
    if _should_ignore(path, ignore):
        return []

    if isinstance(a, dict) and isinstance(b, dict):
        return _diff_dicts(a, b, path, ignore)
    if isinstance(a, list) and isinstance(b, list):
        return _diff_lists(a, b, path, ignore)

    if a == b:
        return [Change(path=path, change_type=ChangeType.UNCHANGED, old_value=a, new_value=b)]
    return [Change(path=path, change_type=ChangeType.MODIFIED, old_value=a, new_value=b)]


def _diff_dicts(
    a: dict[str, Any], b: dict[str, Any], path: str, ignore: set[str]
) -> list[Change]:
    changes: list[Change] = []
    all_keys = sorted(set(a.keys()) | set(b.keys()))

    for key in all_keys:
        child_path = f"{path}.{key}" if path else key

        if _should_ignore(child_path, ignore):
            continue

        if key not in a:
            changes.append(Change(path=child_path, change_type=ChangeType.ADDED, new_value=b[key]))
        elif key not in b:
            changes.append(Change(path=child_path, change_type=ChangeType.REMOVED, old_value=a[key]))
        else:
            changes.extend(_diff_values(a[key], b[key], child_path, ignore))

    return changes


def _diff_lists(
    a: list[Any], b: list[Any], path: str, ignore: set[str]
) -> list[Change]:
    changes: list[Change] = []
    max_len = max(len(a), len(b))

    for i in range(max_len):
        child_path = f"{path}[{i}]"

        if i >= len(a):
            changes.append(Change(path=child_path, change_type=ChangeType.ADDED, new_value=b[i]))
        elif i >= len(b):
            changes.append(Change(path=child_path, change_type=ChangeType.REMOVED, old_value=a[i]))
        else:
            changes.extend(_diff_values(a[i], b[i], child_path, ignore))

    return changes


def format_diff(changes: list[Change], color: bool = True) -> str:
    """Format a list of changes as a human-readable string.

    Args:
        changes: List of Change objects from diff().
        color: Whether to use ANSI color codes.

    Returns:
        Formatted string with +/- prefixes.
    """
    red = "\033[31m" if color else ""
    green = "\033[32m" if color else ""
    yellow = "\033[33m" if color else ""
    reset = "\033[0m" if color else ""

    lines: list[str] = []
    for change in changes:
        match change.change_type:
            case ChangeType.ADDED:
                lines.append(f"{green}+ {change.path}: {_fmt(change.new_value)}{reset}")
            case ChangeType.REMOVED:
                lines.append(f"{red}- {change.path}: {_fmt(change.old_value)}{reset}")
            case ChangeType.MODIFIED:
                lines.append(f"{yellow}~ {change.path}: {_fmt(change.old_value)} → {_fmt(change.new_value)}{reset}")
            case ChangeType.UNCHANGED:
                pass

    return "\n".join(lines) if lines else "No changes"


def _fmt(value: Any) -> str:
    if isinstance(value, str):
        return f'"{value}"'
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def diff_summary(changes: list[Change]) -> dict[str, int]:
    """Return counts of each change type.

    Args:
        changes: List of Change objects from diff().

    Returns:
        Dict mapping change type names to counts.
    """
    summary: dict[str, int] = {t.value: 0 for t in ChangeType}
    for change in changes:
        summary[change.change_type.value] += 1
    return summary
