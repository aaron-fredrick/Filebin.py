# Contributing to Filebin.py

First off, thanks for taking the time to contribute! 🎉

## Development Setup

1. **Fork and Clone** the repository.
2. **Install dependencies** (in a virtual environment):
   ```bash
   pip install -e ".[dev]"
   ```

## Workflow

- **Branching**: Create a feature branch from `main`.
- **Code Style**: We use `ruff` to enforce code quality and formatting.
  * Before committing, format and lint your code:
    ```bash
    ruff check Filebin/ tests/ --fix
    ```
- **Testing**: Ensure all tests pass.
  * Run offline unit tests:
    ```bash
    pytest -m "not network"
    ```
  * Run full integration tests (requires network access):
    ```bash
    pytest
    ```
- **Commit Messages**: Write clear, concise commit messages.

## Pull Requests

1. Submit a PR against the `main` branch.
2. The CI workflow will automatically run `ruff` and the offline unit tests.
3. Once the CI passes and the PR is approved, it will be merged.

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.
