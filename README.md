# philiprehberger-json-diff

[![Tests](https://github.com/philiprehberger/py-json-diff/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-json-diff/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-json-diff.svg)](https://pypi.org/project/philiprehberger-json-diff/)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-json-diff)](https://github.com/philiprehberger/py-json-diff/commits/main)

Readable JSON comparison with colorized terminal output.

## Installation

```bash
pip install philiprehberger-json-diff
```

## Usage

```python
from philiprehberger_json_diff import diff, format_diff, diff_summary

old = {"name": "Alice", "age": 30, "city": "NYC"}
new = {"name": "Alice", "age": 31, "country": "US"}

changes = diff(old, new)

# Pretty-print with colors
print(format_diff(changes))

# Get a summary
summary = diff_summary(changes)
# {"added": 1, "removed": 1, "modified": 1, "total": 3}
```

### Nested Comparison

```python
from philiprehberger_json_diff import diff

old = {"user": {"name": "Alice", "settings": {"theme": "dark"}}}
new = {"user": {"name": "Alice", "settings": {"theme": "light"}}}

changes = diff(old, new)
# Reports: modified user.settings.theme: 'dark' -> 'light'
```

### Ignore Paths

```python
from philiprehberger_json_diff import diff

changes = diff(old, new, ignore={"user.settings.theme"})
```

### Wildcard Ignore Patterns

```python
from philiprehberger_json_diff import diff

old = {"a": {"metadata": {"ts": 1}}, "b": {"metadata": {"ts": 2}}}
new = {"a": {"metadata": {"ts": 99}}, "b": {"metadata": {"ts": 99}}}

# Ignore metadata fields at any depth
changes = diff(old, new, ignore={"*.metadata.*"})
```

### Structural Diff Mode

```python
from philiprehberger_json_diff import diff

old = {"a": 1, "b": "hello", "c": 3}
new = {"a": "one", "b": "world", "d": 4}

result = diff(old, new, mode="structural")
result.key_additions   # [Change(path='d', ...)]
result.key_removals    # [Change(path='c', ...)]
result.value_changes   # [Change(path='b', ...)]
result.type_changes    # [Change(path='a', ...)]
```

### Apply Patch

```python
from philiprehberger_json_diff import diff, apply_patch

old = {"name": "Alice", "age": 30}
new = {"name": "Bob", "age": 31}

changes = diff(old, new)
result = apply_patch(old, changes)
# result == {"name": "Bob", "age": 31}
```

## API

| Function / Class | Description |
|------------------|-------------|
| `diff(a, b, ignore, mode)` | Compare two dicts/lists, returns list of `Change` objects or `StructuralDiff` |
| `format_diff(changes, color)` | Format changes as readable string with optional ANSI colors |
| `diff_summary(changes)` | Return dict with counts by change type |
| `apply_patch(target, changes)` | Apply a diff result as a patch to reconstruct the modified object |
| `Change` | Dataclass with `path`, `change_type`, `old_value`, `new_value` |
| `ChangeType` | Enum: `ADDED`, `REMOVED`, `MODIFIED`, `UNCHANGED` |
| `StructuralDiff` | Dataclass with `key_additions`, `key_removals`, `value_changes`, `type_changes` |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Support

If you find this project useful:

⭐ [Star the repo](https://github.com/philiprehberger/py-json-diff)

🐛 [Report issues](https://github.com/philiprehberger/py-json-diff/issues?q=is%3Aissue+is%3Aopen+label%3Abug)

💡 [Suggest features](https://github.com/philiprehberger/py-json-diff/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

❤️ [Sponsor development](https://github.com/sponsors/philiprehberger)

🌐 [All Open Source Projects](https://philiprehberger.com/open-source-packages)

💻 [GitHub Profile](https://github.com/philiprehberger)

🔗 [LinkedIn Profile](https://www.linkedin.com/in/philiprehberger)

## License

[MIT](LICENSE)
