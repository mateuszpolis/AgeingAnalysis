# Conventional Commits & Automatic Versioning

This project uses [Conventional Commits](https://www.conventionalcommits.org/) to automatically generate versions and releases.

## Commit Message Format

Each commit message consists of a **type**, an optional **scope**, and a **subject**:

```
<type>(<scope>): <subject>
```

### Types

- **feat**: A new feature (triggers MINOR version bump)
- **fix**: A bug fix (triggers PATCH version bump)
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to our CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Breaking Changes

To indicate a breaking change, add `!` after the type/scope or include `BREAKING CHANGE:` in the footer:

```
feat!: remove deprecated API
feat(api)!: remove deprecated endpoint
```

Or:

```
feat(api): add new endpoint

BREAKING CHANGE: The old endpoint has been removed
```

### Examples

```bash
# Feature additions (MINOR version bump)
feat: add CSV export functionality
feat(parser): support new data format
feat(gui): add dark mode toggle

# Bug fixes (PATCH version bump)
fix: resolve calculation error in ageing factors
fix(plotting): fix axis scaling issues
fix(config): handle missing configuration files

# Documentation updates
docs: update installation instructions
docs(api): add API documentation

# Development changes
build: update dependencies
ci: add automated testing
chore: update development tools
```

## Automatic Versioning

The project uses [Commitizen](https://commitizen-tools.github.io/commitizen/) for automatic semantic versioning:

- **PATCH** (x.y.Z): `fix:` commits increment the patch version by 0.0.1
- **MINOR** (x.Y.0): `feat:` commits increment the minor version by 0.1.0
- **MAJOR** (X.0.0): commits with breaking changes increment the major version by 1.0.0

For example:
- `fix: resolve parsing bug` → version 1.2.3 → 1.2.4
- `feat: add new CSV export` → version 1.2.3 → 1.3.0
- `feat!: remove deprecated API` → version 1.2.3 → 2.0.0

## How to Use

### Option 1: Manual Commit Messages

Write your commit messages following the conventional format:

```bash
git add .
git commit -m "feat(parser): add support for new CSV format"
git push
```

### Option 2: Interactive Commit Tool

Use commitizen's interactive tool to create proper commit messages:

```bash
# Install commitizen (if not already installed)
pip install commitizen

# Create a commit interactively
cz commit
```

This will guide you through:
1. Selecting the change type
2. Specifying the scope (optional)
3. Writing the subject line
4. Adding a body description (optional)
5. Noting any breaking changes

### Option 3: Pre-commit Hook

The project includes **strict** pre-commit hooks that validate commit messages. **All commits MUST follow the conventional commit format** - non-conventional commits will be rejected.

The validation includes:
- **Commitizen validation**: Ensures the commit message follows the exact conventional commit format
- **Conventional pre-commit validation**: Additional validation for commit message structure
- **Required format**: `<type>(<scope>): <subject>`

#### Allowed commit types:
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions/changes
- `build`: Build system changes
- `ci`: CI configuration changes
- `chore`: Maintenance tasks
- `revert`: Revert previous commits

#### Examples of REJECTED commits:
```bash
git commit -m "update readme"           # ❌ Missing type
git commit -m "added new feature"       # ❌ Wrong format
git commit -m "Fix bug in parser"       # ❌ Capitalized type
git commit -m "feature: add export"     # ❌ Wrong type name
```

#### Examples of ACCEPTED commits:
```bash
git commit -m "feat: add CSV export functionality"
git commit -m "fix: resolve parsing error"
git commit -m "docs: update installation guide"
git commit -m "feat(parser): support new data format"
```

## Release Process

### Automatic Releases

When you push to the `main` branch:

1. **GitHub Actions** checks for conventional commits
2. If commits are found, **Commitizen** automatically:
   - Bumps the version in `pyproject.toml` and `__init__.py`
   - Updates the `CHANGELOG.md`
   - Creates a git tag
   - Pushes the changes back to the repository
3. **GitHub Actions** then:
   - Creates a GitHub release
   - Builds and attaches zip packages
   - Optionally publishes to PyPI

### Manual Version Bump

You can also manually bump versions:

```bash
# Bump version automatically based on commits
cz bump

# Bump specific version types
cz bump --increment PATCH
cz bump --increment MINOR
cz bump --increment MAJOR

# Dry run to see what would happen
cz bump --dry-run
```

### Release Artifacts

Each release includes:

1. **Source Code Archive**: `ageing-analysis-x.y.z-source.zip`
2. **Complete Package**: `ageing-analysis-x.y.z-complete.zip` (ready-to-use)
3. **Python Wheel**: `ageing_analysis-x.y.z-py3-none-any.whl`
4. **Source Distribution**: `ageing-analysis-x.y.z.tar.gz`

## Best Practices

1. **Write clear, descriptive commit messages**
2. **Use appropriate scopes** (e.g., `parser`, `gui`, `services`)
3. **One logical change per commit**
4. **Test your changes** before committing
5. **Use breaking change markers** when appropriate
6. **Keep the scope short** and meaningful

## Troubleshooting

### Commit Message Rejected

If your commit message is rejected:

```bash
# Check what's wrong
cz check --commit-msg-file .git/COMMIT_EDITMSG

# Fix and recommit
git commit --amend -m "feat(parser): add new CSV support"
```

### Version Not Bumped

If automatic versioning isn't working:

1. Check that your commits follow the conventional format
2. Ensure you're pushing to the `main` branch
3. Check GitHub Actions logs for errors
4. Verify no "bump:" commits are blocking the release

### Manual Release

If you need to create a release manually:

```bash
# Create a new version
cz bump

# Push the changes and tags
git push origin main --tags
```

The GitHub Actions workflow will then create the release automatically.
