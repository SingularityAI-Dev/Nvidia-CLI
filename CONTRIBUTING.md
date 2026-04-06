# Contributing to NVIDIA CLI

Thank you for your interest in contributing to NVIDIA CLI! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code. Please report unacceptable behavior by opening an issue.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a branch for your changes
4. Make your changes and test them
5. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/Nvidia-CLI.git
cd Nvidia-CLI

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
nv --help
```

### Prerequisites

- Python 3.9+
- An NVIDIA API key (get one at [build.nvidia.com](https://build.nvidia.com/explore))

### Running Tests

```bash
pytest
pytest --cov=nv_cli           # With coverage
```

### Linting & Type Checking

```bash
black nv_cli/                  # Format code
mypy nv_cli/ --ignore-missing-imports  # Type check
python -m py_compile nv.py     # Syntax check legacy file
```

## How to Contribute

### Types of Contributions

- **Bug fixes** — Find and fix issues
- **New features** — Add new commands, tools, skills, or agent capabilities
- **Documentation** — Improve docs, add examples, fix typos
- **Tests** — Increase test coverage
- **Skills** — Create new installable skills for the skills system
- **Models** — Add support for new NVIDIA-hosted models

### Good First Issues

Look for issues labeled [`good first issue`](https://github.com/SingularityAI-Dev/Nvidia-CLI/labels/good%20first%20issue) — these are specifically curated for new contributors.

## Pull Request Process

1. **Branch naming**: Use descriptive branch names
   - `feature/agent-collaboration`
   - `fix/memory-search-crash`
   - `docs/improve-readme`

2. **Commit messages**: Write clear, concise commit messages
   ```
   feat: add multi-agent collaboration support
   fix: resolve memory search crash on empty database
   docs: add examples for skill installation
   ```

3. **Before submitting**:
   - Ensure your code follows the project's style conventions
   - Add or update tests if applicable
   - Update documentation if you changed public APIs
   - Run the linter and type checker
   - Make sure all existing tests pass

4. **PR description**: Include:
   - What the change does and why
   - How to test it
   - Screenshots or terminal output if relevant
   - Any breaking changes

5. **Review**: A maintainer will review your PR. Be responsive to feedback and make requested changes promptly.

## Code Style

- **Formatter**: [Black](https://black.readthedocs.io/) with 100 character line length
- **Type hints**: Use type annotations for function signatures
- **Docstrings**: Use docstrings for public functions and classes
- **Imports**: Group imports in order: stdlib, third-party, local

### Project Structure

When adding new features, follow the existing modular structure:

```
nv_cli/
├── agents/      # Agent logic and orchestration
├── config/      # Configuration management
├── heartbeat/   # Periodic task system
├── memory/      # Persistent memory and search
├── skills/      # Skill discovery and management
├── soul/        # Identity and personality system
├── tools/       # Tool registry and implementations
└── utils/       # Shared utilities
```

Each module should:
- Have an `__init__.py` with clean public exports
- Contain focused, single-responsibility files
- Avoid circular imports between modules

## Reporting Bugs

When filing a bug report, include:

1. **Python version**: `python3 --version`
2. **OS and version**: macOS, Linux distro, etc.
3. **CLI version**: `nv --help` (shown in header)
4. **Steps to reproduce**: Exact commands you ran
5. **Expected behavior**: What you expected to happen
6. **Actual behavior**: What actually happened
7. **Error output**: Full traceback if applicable

Use the [bug report template](https://github.com/SingularityAI-Dev/Nvidia-CLI/issues/new?template=bug_report.md) if available.

## Suggesting Features

Feature requests are welcome! Please:

1. Check [existing issues](https://github.com/SingularityAI-Dev/Nvidia-CLI/issues) first to avoid duplicates
2. Describe the use case — what problem does it solve?
3. Propose an interface — what would the commands look like?
4. Consider backwards compatibility

Use the [feature request template](https://github.com/SingularityAI-Dev/Nvidia-CLI/issues/new?template=feature_request.md) if available.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

Thank you for helping make NVIDIA CLI better!
