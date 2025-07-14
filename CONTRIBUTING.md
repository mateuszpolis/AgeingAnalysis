# Contributing to AgeingAnalysis

Welcome! We're excited that you're interested in contributing to the AgeingAnalysis module. This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Understanding of FIT detector physics (helpful but not required)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/AgeingAnalysis.git
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

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation.

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

**Examples:**
```
feat: add Gaussian fitting service
fix: resolve data parser memory leak
docs: update API documentation for plotting module
test: add unit tests for reference channel service
refactor: improve error handling in analysis pipeline
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

3. **Test Your Changes**
   ```bash
   # Run all tests
   pytest

   # Run specific test categories
   pytest -m unit
   pytest -m integration

   # Check code coverage
   pytest --cov=ageing_analysis --cov-report=html
   ```

4. **Run Pre-commit Checks**
   ```bash
   pre-commit run --all-files
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - Use the PR template
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
- Documentation is auto-generated from docstrings
- Ensure docstrings are comprehensive and accurate

## Issue Guidelines

### Bug Reports
- Use the bug report template
- Include reproduction steps
- Provide environment details
- Include error messages and stack traces

### Feature Requests
- Use the feature request template
- Explain the use case
- Provide implementation suggestions if you have them

## Release Process

Releases are automated using conventional commits:

1. **Automatic Versioning**
   - `feat:` commits trigger minor version bumps
   - `fix:` commits trigger patch version bumps
   - `BREAKING CHANGE:` triggers major version bumps

2. **Release Notes**
   - Generated automatically from conventional commits
   - Include all changes since last release

3. **Distribution**
   - Automated builds and tests
   - Automatic PyPI publication (if configured)
   - GitHub releases with artifacts

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

## Migration Guidelines

When migrating code from the `/old` directory:
1. Follow the new module structure
2. Update imports and dependencies
3. Add proper type hints and docstrings
4. Write comprehensive tests
5. Update documentation

Thank you for contributing to AgeingAnalysis! 🚀
