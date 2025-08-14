# Contributing to AgeingAnalysis

[← Back to main README](README.md)

This document provides guidelines for contributing to the project.

## Collaboration Guidelines

Please keep contributions respectful and constructive. Reviews and discussions should focus on technical quality and clarity. This project is maintained primarily for internal use, so processes are intentionally lightweight.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Understanding of FIT detector physics (helpful but not required)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/mateuszpolis/AgeingAnalysis.git
   cd AgeingAnalysis
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e .[dev]
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

5. **Run Tests**
   ```bash
   pytest
   ```

## Development Workflow

### Branch Naming

Use descriptive branch names following this pattern:
- `feature/description-of-feature`
- `bugfix/description-of-fix`
- `hotfix/critical-fix`
- `docs/documentation-update`
- `refactor/code-improvement`

Examples:
- `feature/add-gaussian-fitting`
- `bugfix/fix-data-parser-crash`
- `docs/update-api-documentation`

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation. All commits MUST follow this format — non-conforming commits may be rejected by hooks/CI.

**Format:** `<type>[optional scope]: <description>`

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code changes that neither fix a bug nor add a feature
- `perf`: Performance improvements
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools
 - `ci`: CI configuration changes
 - `build`: Build system or dependency changes
 - `revert`: Revert previous commits

**Examples:**
```
feat: add Gaussian fitting service
fix: resolve data parser memory leak
docs: update API documentation for plotting module
test: add unit tests for reference channel service
refactor: improve error handling in analysis pipeline
```

#### Breaking changes

Indicate with `!` after the type/scope or include `BREAKING CHANGE:` in the footer.

Examples:
```
feat!: remove deprecated API
feat(api)!: change endpoint structure
```
Or:
```
feat(api): add new endpoint

BREAKING CHANGE: The old endpoint has been removed
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Tests and Hooks**
   - Ensure pre-commit hooks are installed (see Getting Started). They will run tests automatically on commit; you do not need to run tests manually.

4. **Optional: Check Code Coverage**
   ```bash
   pytest --cov=ageing_analysis --cov-report=html
   # Then open the HTML report in your browser:
   # htmlcov/index.html
   ```

5. **Run Pre-commit Checks**
   ```bash
   pre-commit run --all-files
   ```

6. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

7. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create Pull Request**
   - Use the provided PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
   - Link to relevant issues
   - Provide clear description of changes

## Code Style Guidelines

### Python Style
- Follow PEP 8 with 88-character line length
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Use Google-style docstrings

### Example Code Style
```python
"""Module docstring."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ExampleClass:
    """Example class with proper documentation.

    Args:
        param1: Description of parameter 1.
        param2: Description of parameter 2.
    """

    def __init__(self, param1: str, param2: Optional[int] = None) -> None:
        """Initialize the class."""
        self.param1 = param1
        self.param2 = param2

    def example_method(self, data: List[float]) -> float:
        """Calculate something from the data.

        Args:
            data: List of input values.

        Returns:
            Calculated result.

        Raises:
            ValueError: If data is empty.
        """
        if not data:
            raise ValueError("Data cannot be empty")

        return sum(data) / len(data)
```

## Testing Guidelines

### Test Structure
- Unit tests: Test individual functions/methods
- Integration tests: Test component interactions
- GUI tests: Test user interface components

### Test Naming
```python
def test_should_calculate_mean_when_given_valid_data():
    """Test that mean calculation works with valid input."""
    # Test implementation
```

### Test Organization
```
tests/
├── unit/
│   ├── test_services/
│   ├── test_gui/
│   └── test_utils/
├── integration/
│   ├── test_analysis_pipeline/
│   └── test_gui_integration/
└── conftest.py
```

## Documentation

### Code Documentation
- All public functions must have docstrings
- Use Google-style docstrings
- Include type hints
- Document parameters, return values, and exceptions

### README Updates
- Update README.md if you add new features
- Include usage examples
- Update installation instructions if needed

### API Documentation
- Location: the `docs/` directory (Sphinx)
- Source: auto-generated from docstrings where applicable
- Build locally:
  ```bash
  make -C docs html
  # then open docs/_build/html/index.html
  ```
- Ensure docstrings are comprehensive and accurate

## Issue Guidelines

When opening an issue, please use the provided templates for consistency:

- **Bug Reports**: Use `.github/ISSUE_TEMPLATE/bug_report.md`
- **Feature Requests**: Use `.github/ISSUE_TEMPLATE/feature_request.md`

These templates will guide you to provide all necessary information:

- Bug reports: Steps to reproduce, expected vs actual behavior, environment details, logs/errors, and config snippets
- Feature requests: Use case, motivation, desired behavior, and optional implementation suggestions

## Release Process

We use semantic-release/commitizen for automated versioning and releases.

### Automatic versioning
- `fix:` → PATCH (x.y.Z)
- `feat:` → MINOR (x.Y.0)
- `BREAKING CHANGE:` or `!` → MAJOR (X.0.0)

### How releases are created
On pushes to `main` (after tests pass):
1. Commits are analyzed to determine the next version
2. Version is bumped (e.g., in `pyproject.toml` and `ageing_analysis/__init__.py` if configured)
3. `CHANGELOG.md` is updated
4. A Git tag is created
5. A GitHub release is created with artifacts (wheel/sdist, archives)

### Local helpers
If using Commitizen:
```
pip install commitizen
cz commit           # guided commit creation
cz bump             # bump version locally (optional)
cz bump --dry-run   # preview version bump
```

### Example commit messages
```
feat(parser): support new CSV format
fix(plotting): correct axis scaling
docs: update installation instructions
feat!: change API structure
```

## Getting Help

- **Questions**: Open a GitHub issue with the "question" label
- **Discussions**: Use GitHub Discussions for general questions
- **Documentation**: Check the README and API documentation
- **Code Review**: All PRs receive code review feedback

## Recognition

Contributors are recognized in:
- CHANGELOG.md
- GitHub contributors list
- Release notes

## Project Structure

```
AgeingAnalysis/
├── ageing_analysis/          # Main package
│   ├── config/              # Configuration management
│   ├── services/            # Core analysis services
│   ├── gui/                 # GUI components
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── docs/                    # Documentation
├── .github/                 # GitHub workflows and templates
├── old/                     # Legacy code (reference only)
└── scripts/                 # Development scripts
```

Thank you for contributing to AgeingAnalysis!
