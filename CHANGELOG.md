# Changelog

## 0.2.1 (2026-03-31)

- Standardize README to 3-badge format with emoji Support section
- Update CI checkout action to v5 for Node.js 24 compatibility

## 0.2.0

- Add wildcard path ignore patterns (e.g. `*.metadata.*`) for ignoring fields at any depth
- Add structural diff mode (`mode="structural"`) that separates key additions/removals from value/type changes
- Add `apply_patch(target, changes)` function to apply a diff result as a patch

## 0.1.5

- Add Development section to README

## 0.1.2

- Fix tests to match actual API (change_type, old_value/new_value fields)

## 0.1.1

- Add project URLs to pyproject.toml

## 0.1.0 (2026-03-10)

- Initial release
- Deep nested JSON comparison with path tracking
- Colorized terminal output
- Ignore keys option
- Diff summary counts
