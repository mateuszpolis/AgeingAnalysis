# Semantic Release Setup

This repository now uses [semantic-release](https://github.com/semantic-release/semantic-release) for automated versioning and releases.

## Setup Steps

1. **Update package.json**: Edit the `repository.url` field in `package.json` to match your actual repository URL.

2. **Commit Message Format**: Use conventional commits for all your commits:
   - `feat:` for new features (minor version bump)
   - `fix:` for bug fixes (patch version bump)
   - `feat!:` or `fix!:` for breaking changes (major version bump)
   - `chore:`, `docs:`, `refactor:`, `test:`, `ci:` for other changes (no version bump)

3. **Examples**:
   ```
   feat: add configuration generator widget
   fix: resolve modal window interaction issues
   feat!: change API structure (breaking change)
   chore: update dependencies
   docs: update README with new features
   ```

## How It Works

1. **Automatic Releases**: When you push to the `main` branch, semantic-release:
   - Analyzes your commit messages
   - Determines the next version number
   - Generates a changelog
   - Creates a Git tag
   - Creates a GitHub release with assets
   - Updates version in Python files

2. **Test Integration**: Tests must pass before releases are created.

3. **Assets**: Each release includes:
   - Python wheel (.whl)
   - Source distribution (.tar.gz)
   - Automatic changelog
   - Release notes

## Configuration Files

- `.releaserc.json`: Semantic-release configuration
- `package.json`: Node.js dependencies for semantic-release
- `scripts/update_version.py`: Script to update version in Python files
- `.github/workflows/release.yml`: GitHub Actions workflow

## First Release

After setting up, make a commit with a conventional commit message:

```bash
git add .
git commit -m "feat: set up semantic-release automation"
git push origin main
```

This will trigger the first automated release.

## Manual Release (if needed)

If you need to trigger a release manually:

```bash
npm install
npx semantic-release --dry-run  # Preview what would happen
npx semantic-release           # Actually create the release
```

## Important Notes

- The version in `pyproject.toml` and `ageing_analysis/__init__.py` will be automatically updated
- Don't manually edit version numbers - let semantic-release handle it
- The `[skip ci]` tag is automatically added to release commits to avoid infinite loops
- Breaking changes should be clearly marked with `!` in the commit message
