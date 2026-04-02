from philiprehberger_json_diff import (
    ArrayStrategy,
    Change,
    ChangeType,
    StructuralDiff,
    apply_patch,
    diff,
    diff_summary,
    format_diff,
    format_html,
    to_json_patch,
)


# ---------------------------------------------------------------------------
# Basic diff
# ---------------------------------------------------------------------------


def test_no_changes():
    changes = diff({"a": 1}, {"a": 1})
    actual = [c for c in changes if c.change_type != ChangeType.UNCHANGED]
    assert actual == []


def test_added_key():
    changes = diff({"a": 1}, {"a": 1, "b": 2})
    added = [c for c in changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].path == "b"


def test_removed_key():
    changes = diff({"a": 1, "b": 2}, {"a": 1})
    removed = [c for c in changes if c.change_type == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].path == "b"


def test_modified_value():
    changes = diff({"a": 1}, {"a": 2})
    modified = [c for c in changes if c.change_type == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].change_type == ChangeType.MODIFIED
    assert modified[0].old_value == 1
    assert modified[0].new_value == 2


def test_nested_change():
    old = {"user": {"name": "Alice", "age": 30}}
    new = {"user": {"name": "Alice", "age": 31}}
    changes = [c for c in diff(old, new) if c.change_type != ChangeType.UNCHANGED]
    assert len(changes) == 1
    assert changes[0].path == "user.age"


def test_ignore_paths():
    old = {"a": 1, "b": 2}
    new = {"a": 10, "b": 20}
    changes = diff(old, new, ignore={"a"})
    assert len(changes) == 1
    assert changes[0].path == "b"


def test_format_diff_returns_string():
    changes = diff({"a": 1}, {"a": 2})
    result = format_diff(changes, color=False)
    assert isinstance(result, str)
    assert "a" in result


def test_diff_summary():
    changes = diff({"a": 1, "b": 2}, {"a": 10, "c": 3})
    summary = diff_summary(changes)
    assert summary["added"] == 1
    assert summary["removed"] == 1
    assert summary["modified"] == 1


def test_empty_dicts():
    assert diff({}, {}) == []


def test_deeply_nested():
    old = {"a": {"b": {"c": {"d": 1}}}}
    new = {"a": {"b": {"c": {"d": 2}}}}
    changes = [c for c in diff(old, new) if c.change_type != ChangeType.UNCHANGED]
    assert len(changes) == 1
    assert changes[0].path == "a.b.c.d"


# ---------------------------------------------------------------------------
# Wildcard ignore patterns
# ---------------------------------------------------------------------------


def test_wildcard_ignore_star_segment():
    old = {"a": {"metadata": {"x": 1}}, "b": {"metadata": {"y": 2}}}
    new = {"a": {"metadata": {"x": 99}}, "b": {"metadata": {"y": 99}}}
    changes = diff(old, new, ignore={"*.metadata.*"})
    actual = [c for c in changes if c.change_type != ChangeType.UNCHANGED]
    assert actual == []


def test_wildcard_ignore_specific_field():
    old = {"a": {"ts": 1, "val": 10}, "b": {"ts": 2, "val": 20}}
    new = {"a": {"ts": 99, "val": 10}, "b": {"ts": 99, "val": 20}}
    changes = diff(old, new, ignore={"*.ts"})
    actual = [c for c in changes if c.change_type != ChangeType.UNCHANGED]
    assert actual == []


def test_wildcard_does_not_ignore_non_matching():
    old = {"a": {"ts": 1, "val": 10}}
    new = {"a": {"ts": 99, "val": 99}}
    changes = diff(old, new, ignore={"*.ts"})
    actual = [c for c in changes if c.change_type != ChangeType.UNCHANGED]
    assert len(actual) == 1
    assert actual[0].path == "a.val"


# ---------------------------------------------------------------------------
# Structural diff mode
# ---------------------------------------------------------------------------


def test_structural_mode_returns_structural_diff():
    old = {"a": 1, "b": 2}
    new = {"a": 10, "c": 3}
    result = diff(old, new, mode="structural")
    assert isinstance(result, StructuralDiff)


def test_structural_mode_key_additions():
    old = {"a": 1}
    new = {"a": 1, "b": 2}
    result = diff(old, new, mode="structural")
    assert isinstance(result, StructuralDiff)
    assert len(result.key_additions) == 1
    assert result.key_additions[0].path == "b"
    assert result.key_removals == []
    assert result.value_changes == []
    assert result.type_changes == []


def test_structural_mode_key_removals():
    old = {"a": 1, "b": 2}
    new = {"a": 1}
    result = diff(old, new, mode="structural")
    assert isinstance(result, StructuralDiff)
    assert len(result.key_removals) == 1
    assert result.key_removals[0].path == "b"


def test_structural_mode_value_changes():
    old = {"a": 1}
    new = {"a": 2}
    result = diff(old, new, mode="structural")
    assert isinstance(result, StructuralDiff)
    assert len(result.value_changes) == 1
    assert result.value_changes[0].path == "a"


def test_structural_mode_type_changes():
    old = {"a": 1}
    new = {"a": "one"}
    result = diff(old, new, mode="structural")
    assert isinstance(result, StructuralDiff)
    assert len(result.type_changes) == 1
    assert result.type_changes[0].path == "a"
    assert result.value_changes == []


def test_structural_mode_mixed():
    old = {"a": 1, "b": "hello", "c": 3}
    new = {"a": "one", "b": "world", "d": 4}
    result = diff(old, new, mode="structural")
    assert isinstance(result, StructuralDiff)
    assert len(result.key_additions) == 1  # d added
    assert len(result.key_removals) == 1   # c removed
    assert len(result.value_changes) == 1  # b: hello -> world
    assert len(result.type_changes) == 1   # a: 1 -> "one"


# ---------------------------------------------------------------------------
# apply_patch
# ---------------------------------------------------------------------------


def test_apply_patch_basic():
    old = {"a": 1, "b": 2}
    new = {"a": 10, "c": 3}
    changes = diff(old, new)
    result = apply_patch(old, changes)
    assert result == new


def test_apply_patch_nested():
    old = {"user": {"name": "Alice", "age": 30}}
    new = {"user": {"name": "Bob", "age": 31}}
    changes = diff(old, new)
    result = apply_patch(old, changes)
    assert result == new


def test_apply_patch_add_remove():
    old = {"a": 1, "b": 2}
    new = {"b": 2, "c": 3}
    changes = diff(old, new)
    result = apply_patch(old, changes)
    assert result == new


def test_apply_patch_deeply_nested():
    old = {"a": {"b": {"c": {"d": 1}}}}
    new = {"a": {"b": {"c": {"d": 2}}}}
    changes = diff(old, new)
    result = apply_patch(old, changes)
    assert result == new


def test_apply_patch_does_not_mutate_original():
    old = {"a": 1, "b": 2}
    new = {"a": 10, "c": 3}
    changes = diff(old, new)
    old_copy = {"a": 1, "b": 2}
    apply_patch(old, changes)
    assert old == old_copy


def test_apply_patch_lists():
    old = {"items": [1, 2, 3]}
    new = {"items": [1, 20, 3]}
    changes = diff(old, new)
    result = apply_patch(old, changes)
    assert result == new


def test_apply_patch_list_add():
    old = {"items": [1, 2]}
    new = {"items": [1, 2, 3]}
    changes = diff(old, new)
    result = apply_patch(old, changes)
    assert result == new


def test_apply_patch_empty_changes():
    old = {"a": 1}
    changes = diff(old, old)
    result = apply_patch(old, changes)
    assert result == old


# ---------------------------------------------------------------------------
# RFC 6902 JSON Patch (to_json_patch)
# ---------------------------------------------------------------------------


def test_json_patch_add():
    changes = diff({"a": 1}, {"a": 1, "b": 2})
    patch = to_json_patch(changes)
    ops = [p for p in patch if p["op"] == "add"]
    assert len(ops) == 1
    assert ops[0]["path"] == "/b"
    assert ops[0]["value"] == 2


def test_json_patch_remove():
    changes = diff({"a": 1, "b": 2}, {"a": 1})
    patch = to_json_patch(changes)
    ops = [p for p in patch if p["op"] == "remove"]
    assert len(ops) == 1
    assert ops[0]["path"] == "/b"
    assert "value" not in ops[0]


def test_json_patch_replace():
    changes = diff({"a": 1}, {"a": 2})
    patch = to_json_patch(changes)
    ops = [p for p in patch if p["op"] == "replace"]
    assert len(ops) == 1
    assert ops[0]["path"] == "/a"
    assert ops[0]["value"] == 2


def test_json_patch_nested_path():
    changes = diff(
        {"user": {"name": "Alice"}},
        {"user": {"name": "Bob"}},
    )
    patch = to_json_patch(changes)
    ops = [p for p in patch if p["op"] == "replace"]
    assert ops[0]["path"] == "/user/name"


def test_json_patch_array_index():
    changes = diff({"items": [1, 2]}, {"items": [1, 20]})
    patch = to_json_patch(changes)
    ops = [p for p in patch if p["op"] == "replace"]
    assert ops[0]["path"] == "/items/1"
    assert ops[0]["value"] == 20


def test_json_patch_no_changes():
    changes = diff({"a": 1}, {"a": 1})
    patch = to_json_patch(changes)
    assert patch == []


def test_json_patch_mixed_operations():
    old = {"a": 1, "b": 2}
    new = {"a": 10, "c": 3}
    patch = to_json_patch(diff(old, new))
    ops_by_type = {}
    for p in patch:
        ops_by_type.setdefault(p["op"], []).append(p)
    assert len(ops_by_type.get("replace", [])) == 1
    assert len(ops_by_type.get("remove", [])) == 1
    assert len(ops_by_type.get("add", [])) == 1


def test_json_patch_special_chars_in_key():
    """Keys containing '/' or '~' must be escaped in JSON Pointer."""
    changes = diff({"a/b": 1}, {"a/b": 2})
    patch = to_json_patch(changes)
    assert patch[0]["path"] == "/a~1b"

    changes2 = diff({"a~b": 1}, {"a~b": 2})
    patch2 = to_json_patch(changes2)
    assert patch2[0]["path"] == "/a~0b"


# ---------------------------------------------------------------------------
# Array diff strategies
# ---------------------------------------------------------------------------


def test_order_sensitive_default():
    """Default behaviour: order matters."""
    old = {"items": [1, 2, 3]}
    new = {"items": [3, 2, 1]}
    changes = [c for c in diff(old, new) if c.change_type != ChangeType.UNCHANGED]
    # index 0: 1->3, index 2: 3->1
    assert len(changes) == 2


def test_order_insensitive_no_changes():
    """Same elements in different order should produce no changes."""
    old = {"items": [1, 2, 3]}
    new = {"items": [3, 2, 1]}
    changes = diff(old, new, array_strategy=ArrayStrategy.ORDER_INSENSITIVE)
    actual = [c for c in changes if c.change_type != ChangeType.UNCHANGED]
    assert actual == []


def test_order_insensitive_addition():
    old = {"items": [1, 2]}
    new = {"items": [2, 1, 3]}
    changes = diff(old, new, array_strategy=ArrayStrategy.ORDER_INSENSITIVE)
    added = [c for c in changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].new_value == 3


def test_order_insensitive_removal():
    old = {"items": [1, 2, 3]}
    new = {"items": [3, 1]}
    changes = diff(old, new, array_strategy=ArrayStrategy.ORDER_INSENSITIVE)
    removed = [c for c in changes if c.change_type == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].old_value == 2


def test_order_insensitive_duplicates():
    """Duplicate values should be tracked correctly."""
    old = {"items": [1, 1, 2]}
    new = {"items": [1, 2, 2]}
    changes = diff(old, new, array_strategy=ArrayStrategy.ORDER_INSENSITIVE)
    removed = [c for c in changes if c.change_type == ChangeType.REMOVED]
    added = [c for c in changes if c.change_type == ChangeType.ADDED]
    assert len(removed) == 1
    assert removed[0].old_value == 1
    assert len(added) == 1
    assert added[0].new_value == 2


def test_order_insensitive_empty_to_values():
    old = {"items": []}
    new = {"items": [1, 2]}
    changes = diff(old, new, array_strategy=ArrayStrategy.ORDER_INSENSITIVE)
    added = [c for c in changes if c.change_type == ChangeType.ADDED]
    assert len(added) == 2


def test_order_insensitive_values_to_empty():
    old = {"items": [1, 2]}
    new = {"items": []}
    changes = diff(old, new, array_strategy=ArrayStrategy.ORDER_INSENSITIVE)
    removed = [c for c in changes if c.change_type == ChangeType.REMOVED]
    assert len(removed) == 2


def test_order_insensitive_nested_dicts():
    """Order-insensitive comparison with dict elements uses equality."""
    old = [{"id": 1}, {"id": 2}]
    new = [{"id": 2}, {"id": 1}]
    changes = diff(old, new, array_strategy=ArrayStrategy.ORDER_INSENSITIVE)
    actual = [c for c in changes if c.change_type != ChangeType.UNCHANGED]
    assert actual == []


# ---------------------------------------------------------------------------
# HTML output format (format_html)
# ---------------------------------------------------------------------------


def test_format_html_contains_table():
    changes = diff({"a": 1}, {"a": 2})
    html = format_html(changes)
    assert "<table>" in html
    assert "</table>" in html


def test_format_html_added_row():
    changes = diff({}, {"a": 1})
    html = format_html(changes)
    assert 'class="added"' in html
    assert "<td>+</td>" in html


def test_format_html_removed_row():
    changes = diff({"a": 1}, {})
    html = format_html(changes)
    assert 'class="removed"' in html
    assert "<td>-</td>" in html


def test_format_html_modified_row():
    changes = diff({"a": 1}, {"a": 2})
    html = format_html(changes)
    assert 'class="modified"' in html
    assert "<td>~</td>" in html


def test_format_html_escapes_special_chars():
    changes = diff({"k": "<b>old</b>"}, {"k": "<b>new</b>"})
    html = format_html(changes)
    assert "&lt;b&gt;" in html
    assert "<b>" not in html.replace("<tbody>", "").replace("</tbody>", "")


def test_format_html_no_changes():
    changes = diff({"a": 1}, {"a": 1})
    html = format_html(changes)
    assert "<table>" in html
    # Only header, no data rows
    assert 'class="added"' not in html
    assert 'class="removed"' not in html
    assert 'class="modified"' not in html


def test_format_html_header_columns():
    changes = diff({"a": 1}, {"a": 2})
    html = format_html(changes)
    assert "<th>Op</th>" in html
    assert "<th>Path</th>" in html
    assert "<th>Old</th>" in html
    assert "<th>New</th>" in html


# ---------------------------------------------------------------------------
# Ignore paths (additional coverage)
# ---------------------------------------------------------------------------


def test_ignore_nested_path():
    old = {"user": {"name": "Alice", "age": 30}}
    new = {"user": {"name": "Bob", "age": 31}}
    changes = diff(old, new, ignore={"user.name"})
    actual = [c for c in changes if c.change_type != ChangeType.UNCHANGED]
    assert len(actual) == 1
    assert actual[0].path == "user.age"


def test_ignore_with_list():
    """ignore parameter accepts a list as well as a set."""
    old = {"a": 1, "b": 2}
    new = {"a": 10, "b": 20}
    changes = diff(old, new, ignore=["a"])
    assert len(changes) == 1
    assert changes[0].path == "b"


def test_ignore_multiple_paths():
    old = {"a": 1, "b": 2, "c": 3}
    new = {"a": 10, "b": 20, "c": 30}
    changes = diff(old, new, ignore={"a", "c"})
    assert len(changes) == 1
    assert changes[0].path == "b"
