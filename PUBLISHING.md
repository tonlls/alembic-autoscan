# Publishing to PyPI with UV

## Prerequisites

1. **Create a PyPI account**: https://pypi.org/account/register/
2. **Create an API token**: https://pypi.org/manage/account/token/
   - Give it a descriptive name like "alembic-autoscan"
   - Save the token securely

## Publishing Steps

### 1. Test on TestPyPI First (Recommended)

```bash
# Create TestPyPI account: https://test.pypi.org/account/register/
# Create API token: https://test.pypi.org/manage/account/token/

# Publish to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/
```

When prompted, use:
- Username: `__token__`
- Password: Your TestPyPI API token (starts with `pypi-`)

### 2. Test Installation from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ alembic-autoscan
```

### 3. Publish to Production PyPI

Once you've verified everything works on TestPyPI:

```bash
uv publish
```

When prompted, use:
- Username: `__token__`
- Password: Your PyPI API token

### Alternative: Use Environment Variables

```bash
# Set your token
export UV_PUBLISH_TOKEN=pypi-your-token-here

# Publish without prompts
uv publish
```

## Pre-Publishing Checklist

- [x] Package builds successfully (`uv build`)
- [x] Tests pass (`uv run pytest`)
- [x] README is comprehensive
- [x] Version number is correct in `pyproject.toml`
- [x] CHANGELOG is updated
- [x] GitHub repository URLs are updated in `pyproject.toml`
- [x] License is correct

## Update Package Metadata

Before publishing, update these fields in `pyproject.toml`:

```toml
[project]
authors = [
    {name = "tonlls", email = "tonlls@users.noreply.github.com"}
]

[project.urls]
Homepage = "https://github.com/tonlls/alembic-autoscan"
Repository = "https://github.com/tonlls/alembic-autoscan"
Issues = "https://github.com/tonlls/alembic-autoscan/issues"
```

## Version Management

To release a new version:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create a git tag:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```
5. Rebuild and publish:
   ```bash
   uv build
   uv publish
   ```

## Useful Commands

```bash
# Build the package
uv build

# Check what will be included in the package
tar -tzf dist/alembic_autoscan-0.1.0.tar.gz

# Run tests before publishing
uv run pytest tests/ -v

# Format and lint code
uv run ruff check --fix .
uv run ruff format .

# Type check
uv run mypy alembic_autoscan
```

## Troubleshooting

**"File already exists" error:**
- You can't re-upload the same version to PyPI
- Increment the version number in `pyproject.toml`
- Rebuild with `uv build`

**Authentication errors:**
- Make sure you're using `__token__` as the username
- Verify your API token is correct and has upload permissions

**Package not found after publishing:**
- Wait a few minutes for PyPI to index your package
- Check https://pypi.org/project/alembic-autoscan/

## Current Build Status

✅ **Built successfully!**

Distribution files in `dist/`:
- `alembic_autoscan-0.1.0-py3-none-any.whl` (7.7 KB)
- `alembic_autoscan-0.1.0.tar.gz` (115 KB)

Ready to publish! 🚀
