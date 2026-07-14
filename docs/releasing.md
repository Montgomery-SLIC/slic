# Releasing

SLIC follows [Semantic Versioning](https://semver.org/). The version is the single source of truth in `pyproject.toml` and is read at runtime by `slic/__init__.py`.

## When to bump

| Change | Version bump | Example |
|--------|-------------|---------|
| Bug fix, security patch | `patch` | `1.0.0` - `1.0.1` |
| New feature, backwards-compatible | `minor` | `1.0.0` - `1.1.0` |
| Breaking change to data model or behaviour | `major` | `1.0.0` - `2.0.0` |

## Release steps

```bash
# 1. Make sure you are on main with a clean working tree
git checkout main
git pull origin main

# 2. Bump the version - choose patch, minor, or major
bump-my-version bump minor

# This automatically:
#   - updates version in pyproject.toml
#   - commits: "chore: bump version to 1.1.0"
#   - creates tag: v1.1.0

# 3. Push the commit and tag together
git push --follow-tags origin main
```

The CI workflow runs on push to `main`, so the tag push triggers the test suite. There is no automated deployment - after the tests pass, deploy manually following [deployment.md](deployment.md).

## Checking the current version

```bash
python -c "from slic import __version__; print(__version__)"
```

Or read it directly:

```bash
grep '^version' pyproject.toml
```
