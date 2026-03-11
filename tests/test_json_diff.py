from philiprehberger_json_diff import diff, format_diff, diff_summary, ChangeType


def test_no_changes():
    changes = diff({"a": 1}, {"a": 1})
    assert changes == []


def test_added_key():
    changes = diff({"a": 1}, {"a": 1, "b": 2})
    assert len(changes) == 1
    assert changes[0].type == ChangeType.ADDED
    assert changes[0].path == "b"


def test_removed_key():
    changes = diff({"a": 1, "b": 2}, {"a": 1})
    assert len(changes) == 1
    assert changes[0].type == ChangeType.REMOVED
    assert changes[0].path == "b"


def test_modified_value():
    changes = diff({"a": 1}, {"a": 2})
    assert len(changes) == 1
    assert changes[0].type == ChangeType.MODIFIED
    assert changes[0].old == 1
    assert changes[0].new == 2


def test_nested_change():
    old = {"user": {"name": "Alice", "age": 30}}
    new = {"user": {"name": "Alice", "age": 31}}
    changes = diff(old, new)
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
    assert summary["total"] == 3


def test_empty_dicts():
    assert diff({}, {}) == []


def test_deeply_nested():
    old = {"a": {"b": {"c": {"d": 1}}}}
    new = {"a": {"b": {"c": {"d": 2}}}}
    changes = diff(old, new)
    assert len(changes) == 1
    assert changes[0].path == "a.b.c.d"
