from philiprehberger_json_diff import diff, format_diff, diff_summary, ChangeType


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
