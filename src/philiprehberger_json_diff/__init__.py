"""Readable JSON comparison with colorized terminal output."""

from __future__ import annotations

import copy
import fnmatch
from dataclasses import dataclass
from enum import Enum
from html import escape as html_escape
from typing import Any


__all__ = [
    "ArrayStrategy",
    "Change",
    "ChangeType",
    "StructuralDiff",
    "apply_patch",
    "diff",
    "diff_summary",
    "format_diff",
    "format_html",
    "to_json_patch",
]


class ChangeType(Enum):
    """Type of change detected between two values."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class ArrayStrategy(Enum):
    """Strategy for comparing arrays/lists.

    ``ORDER_SENSITIVE`` (default) compares elements by index position.
    ``ORDER_INSENSITIVE`` treats arrays as unordered collections and matches
    by value equality, reporting the minimal set of additions and removals.
    """

    ORDER_SENSITIVE = "order_sensitive"
    ORDER_INSENSITIVE = "order_insensitive"


@dataclass(frozen=True)
class Change:
    """A single difference between two JSON-compatible objects."""

    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None


@dataclass(frozen=True)
class StructuralDiff:
    """Diff result separated into structural vs value changes."""

    key_additions: list[Change]
    key_removals: list[Change]
    value_changes: list[Change]
    type_changes: list[Change]


def diff(
    a: Any,
    b: Any,
    ignore: set[str] | list[str] | None = None,
    mode: str = "full",
    array_strategy: ArrayStrategy = ArrayStrategy.ORDER_SENSITIVE,
    _path: str = "",
) -> list[Change] | StructuralDiff:
    """Compare two JSON-compatible objects and return a list of changes.

    Args:
        a: The original object.
        b: The new object.
        ignore: Set of dot-path keys or wildcard patterns (e.g. ``*.metadata.*``)
            to ignore.
        mode: ``"full"`` (default) returns a flat list of changes.
            ``"structural"`` returns a :class:`StructuralDiff` separating
            key additions/removals from value/type changes.
        array_strategy: Strategy for comparing arrays. ``ORDER_SENSITIVE``
            (default) compares by index. ``ORDER_INSENSITIVE`` treats arrays
            as unordered collections.
        _path: Internal path prefix for recursion.

    Returns:
        List of Change objects (``mode="full"``) or a :class:`StructuralDiff`
        (``mode="structural"``).
    """
    ignore_set = set(ignore) if ignore else set()
    changes = _diff_values(a, b, _path, ignore_set, array_strategy)

    if mode == "structural":
        return _to_structural(changes)
    return changes


def _has_wildcard(pattern: str) -> bool:
    return "*" in pattern or "?" in pattern or "[" in pattern


def _should_ignore(path: str, ignore: set[str]) -> bool:
    if not ignore:
        return False
    if path in ignore:
        return True

    for pattern in ignore:
        if _has_wildcard(pattern):
            if fnmatch.fnmatch(path, pattern):
                return True
        else:
            # Legacy behaviour: match trailing key name
            parts = path.rsplit(".", 1)
            if len(parts) > 1 and parts[-1] == pattern:
                return True

    return False


def _diff_values(
    a: Any, b: Any, path: str, ignore: set[str], array_strategy: ArrayStrategy
) -> list[Change]:
    if _should_ignore(path, ignore):
        return []

    if isinstance(a, dict) and isinstance(b, dict):
        return _diff_dicts(a, b, path, ignore, array_strategy)
    if isinstance(a, list) and isinstance(b, list):
        if array_strategy == ArrayStrategy.ORDER_INSENSITIVE:
            return _diff_lists_unordered(a, b, path, ignore)
        return _diff_lists(a, b, path, ignore, array_strategy)

    if a == b:
        return [Change(path=path, change_type=ChangeType.UNCHANGED, old_value=a, new_value=b)]
    return [Change(path=path, change_type=ChangeType.MODIFIED, old_value=a, new_value=b)]


def _diff_dicts(
    a: dict[str, Any], b: dict[str, Any], path: str, ignore: set[str],
    array_strategy: ArrayStrategy,
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
            changes.extend(_diff_values(a[key], b[key], child_path, ignore, array_strategy))

    return changes


def _diff_lists(
    a: list[Any], b: list[Any], path: str, ignore: set[str],
    array_strategy: ArrayStrategy,
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
            changes.extend(_diff_values(a[i], b[i], child_path, ignore, array_strategy))

    return changes


def _diff_lists_unordered(
    a: list[Any], b: list[Any], path: str, ignore: set[str],
) -> list[Change]:
    """Compare two lists as unordered collections (set-like diff)."""
    changes: list[Change] = []

    # Track which items in b have been matched
    b_remaining = list(range(len(b)))
    a_matched: list[bool] = [False] * len(a)

    # First pass: find exact matches
    for i, a_item in enumerate(a):
        for j_idx, j in enumerate(b_remaining):
            if a_item == b[j]:
                a_matched[i] = True
                b_remaining.pop(j_idx)
                break

    # Unmatched items in a are removals
    for i, item in enumerate(a):
        if not a_matched[i]:
            child_path = f"{path}[{i}]"
            if not _should_ignore(child_path, ignore):
                changes.append(Change(
                    path=child_path, change_type=ChangeType.REMOVED, old_value=item,
                ))

    # Unmatched items in b are additions
    for j in b_remaining:
        child_path = f"{path}[{j}]"
        if not _should_ignore(child_path, ignore):
            changes.append(Change(
                path=child_path, change_type=ChangeType.ADDED, new_value=b[j],
            ))

    return changes


def _to_structural(changes: list[Change]) -> StructuralDiff:
    """Split a flat change list into structural categories."""
    key_additions: list[Change] = []
    key_removals: list[Change] = []
    value_changes: list[Change] = []
    type_changes: list[Change] = []

    for change in changes:
        if change.change_type == ChangeType.ADDED:
            key_additions.append(change)
        elif change.change_type == ChangeType.REMOVED:
            key_removals.append(change)
        elif change.change_type == ChangeType.MODIFIED:
            if type(change.old_value) is not type(change.new_value):
                type_changes.append(change)
            else:
                value_changes.append(change)

    return StructuralDiff(
        key_additions=key_additions,
        key_removals=key_removals,
        value_changes=value_changes,
        type_changes=type_changes,
    )


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


def format_html(changes: list[Change]) -> str:
    """Format a list of changes as an HTML table for web UIs.

    Args:
        changes: List of Change objects from diff().

    Returns:
        An HTML string containing a ``<table>`` with change rows.
        Added rows have class ``added``, removed rows ``removed``,
        and modified rows ``modified``.
    """
    rows: list[str] = []
    for change in changes:
        match change.change_type:
            case ChangeType.ADDED:
                rows.append(
                    f'<tr class="added">'
                    f"<td>+</td>"
                    f"<td>{html_escape(change.path)}</td>"
                    f"<td></td>"
                    f"<td>{html_escape(_fmt(change.new_value))}</td>"
                    f"</tr>"
                )
            case ChangeType.REMOVED:
                rows.append(
                    f'<tr class="removed">'
                    f"<td>-</td>"
                    f"<td>{html_escape(change.path)}</td>"
                    f"<td>{html_escape(_fmt(change.old_value))}</td>"
                    f"<td></td>"
                    f"</tr>"
                )
            case ChangeType.MODIFIED:
                rows.append(
                    f'<tr class="modified">'
                    f"<td>~</td>"
                    f"<td>{html_escape(change.path)}</td>"
                    f"<td>{html_escape(_fmt(change.old_value))}</td>"
                    f"<td>{html_escape(_fmt(change.new_value))}</td>"
                    f"</tr>"
                )
            case ChangeType.UNCHANGED:
                pass

    header = (
        "<table>"
        "<thead><tr>"
        "<th>Op</th><th>Path</th><th>Old</th><th>New</th>"
        "</tr></thead>"
        "<tbody>"
    )
    footer = "</tbody></table>"
    return header + "".join(rows) + footer


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


# ---------------------------------------------------------------------------
# RFC 6902 JSON Patch
# ---------------------------------------------------------------------------


def _path_to_json_pointer(path: str) -> str:
    """Convert a dot-path with bracket indices to a JSON Pointer (RFC 6901).

    Examples:
        ``"user.name"`` -> ``"/user/name"``
        ``"items[0].name"`` -> ``"/items/0/name"``
    """
    segments = _parse_path(path)
    escaped: list[str] = []
    for seg in segments:
        s = str(seg)
        # JSON Pointer escaping: ~ -> ~0, / -> ~1
        s = s.replace("~", "~0").replace("/", "~1")
        escaped.append(s)
    return "/" + "/".join(escaped) if escaped else ""


def to_json_patch(changes: list[Change]) -> list[dict[str, Any]]:
    """Convert a list of changes to RFC 6902 JSON Patch format.

    Args:
        changes: List of Change objects from diff().

    Returns:
        A list of JSON Patch operation dicts. Each dict has an ``op`` key
        (``"add"``, ``"remove"``, or ``"replace"``) and a ``path`` key
        in JSON Pointer format. ``"add"`` and ``"replace"`` operations
        include a ``value`` key.

    Example::

        patch = to_json_patch(diff(old, new))
        # [{"op": "replace", "path": "/age", "value": 31}, ...]
    """
    ops: list[dict[str, Any]] = []

    for change in changes:
        pointer = _path_to_json_pointer(change.path)
        match change.change_type:
            case ChangeType.ADDED:
                ops.append({"op": "add", "path": pointer, "value": change.new_value})
            case ChangeType.REMOVED:
                ops.append({"op": "remove", "path": pointer})
            case ChangeType.MODIFIED:
                ops.append({"op": "replace", "path": pointer, "value": change.new_value})
            case ChangeType.UNCHANGED:
                pass

    return ops


# ---------------------------------------------------------------------------
# apply_patch
# ---------------------------------------------------------------------------


def apply_patch(target: Any, changes: list[Change]) -> Any:
    """Apply a diff result as a patch to reconstruct the modified object.

    Takes a target object and a list of changes (as returned by
    ``diff(a, b)``), then applies the additions, removals, and
    modifications to produce the patched object.

    Args:
        target: The base object to patch (will not be mutated).
        changes: List of Change objects to apply.

    Returns:
        A new object with all changes applied.
    """
    result = copy.deepcopy(target)

    # Sort changes so removals are processed last (to avoid index shifts in lists)
    # and additions/modifications first.
    additions = [c for c in changes if c.change_type == ChangeType.ADDED]
    modifications = [c for c in changes if c.change_type == ChangeType.MODIFIED]
    removals = [c for c in changes if c.change_type == ChangeType.REMOVED]

    for change in modifications:
        _apply_change(result, change)

    for change in additions:
        _apply_change(result, change)

    # Process removals in reverse path order so list indices stay valid
    for change in sorted(removals, key=lambda c: c.path, reverse=True):
        _apply_removal(result, change)

    return result


def _parse_path(path: str) -> list[str | int]:
    """Parse a dotted path with bracket indices into segments."""
    segments: list[str | int] = []
    current = ""
    i = 0
    while i < len(path):
        ch = path[i]
        if ch == ".":
            if current:
                segments.append(current)
                current = ""
        elif ch == "[":
            if current:
                segments.append(current)
                current = ""
            j = path.index("]", i)
            segments.append(int(path[i + 1 : j]))
            i = j
        else:
            current += ch
        i += 1
    if current:
        segments.append(current)
    return segments


def _apply_change(obj: Any, change: Change) -> None:
    """Set a value at the given change path."""
    segments = _parse_path(change.path)
    target = obj
    for seg in segments[:-1]:
        if isinstance(seg, int):
            target = target[seg]
        else:
            target = target[seg]
    last = segments[-1]
    if isinstance(target, list) and isinstance(last, int):
        if last >= len(target):
            target.append(change.new_value)
        else:
            target[last] = change.new_value
    else:
        target[last] = change.new_value


def _apply_removal(obj: Any, change: Change) -> None:
    """Remove a value at the given change path."""
    segments = _parse_path(change.path)
    target = obj
    for seg in segments[:-1]:
        target = target[seg]
    last = segments[-1]
    if isinstance(target, list) and isinstance(last, int):
        if last < len(target):
            del target[last]
    elif isinstance(target, dict) and isinstance(last, str):
        target.pop(last, None)
