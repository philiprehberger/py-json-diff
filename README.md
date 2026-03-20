# philiprehberger-json-diff

[![Tests](https://github.com/philiprehberger/py-json-diff/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-json-diff/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-json-diff.svg)](https://pypi.org/project/philiprehberger-json-diff/)
[![License](https://img.shields.io/github/license/philiprehberger/py-json-diff)](LICENSE)

Readable JSON/dict comparison with colorized terminal output.

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
old = {"user": {"name": "Alice", "settings": {"theme": "dark"}}}
new = {"user": {"name": "Alice", "settings": {"theme": "light"}}}

changes = diff(old, new)
# Reports: modified user.settings.theme: 'dark' -> 'light'
```

### Ignore Paths

```python
changes = diff(old, new, ignore={"user.settings.theme"})
```

## API

| Function / Class | Description |
|------------------|-------------|
| `diff(old, new, ignore=None)` | Compare two dicts, returns list of `Change` objects |
| `format_diff(changes, color=True)` | Format changes as readable string with optional ANSI colors |
| `diff_summary(changes)` | Return dict with counts by change type |


## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
