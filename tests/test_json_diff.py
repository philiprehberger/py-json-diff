from philiprehberger_json_diff import (
    diff,
    format_diff,
    diff_summary,
    apply_patch,
    ChangeType,
    StructuralDiff,
)


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


# --- Wildcard ignore patterns ---


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


# --- Structural diff mode ---


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


# --- apply_patch ---


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
