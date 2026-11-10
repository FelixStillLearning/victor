# Contributing to V.I.C.T.O.R.

Thank you for your interest in contributing to V.I.C.T.O.R. This project adheres to high standards of code clarity, performance, and Linux desktop integration.

---

## Code of Conduct

All contributors are expected to uphold a professional, respectful, and constructive environment. Harassment, condescending behavior, or dismissive discourse will not be tolerated.

---

## Development Workflow

1. Fork the repository and create a descriptive branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Set up a virtual development environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,vision]"
   ```
3. Ensure formatting and static analysis checks pass:
   ```bash
   ruff check .
   black --check .
   mypy src/victor
   ```
4. Run the automated test suite:
   ```bash
   pytest tests/ -v
   ```

---

## Commit Message Convention

Commits must follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) specification:

* `feat(scope): add new feature or plugin`
* `fix(scope): resolve bug or unhandled edge case`
* `docs(scope): documentation updates or architectural diagrams`
* `refactor(scope): internal code restructuring without changing external behavior`
* `perf(scope): latency, memory, or throughput improvements`
* `test(scope): add or improve test coverage`

---

## Plugin Development Standards

All new functional capabilities must be implemented as modular plugins adhering to `VictorPlugin`:
* Implement `name`, `keywords`, `setup()`, and `handle()`.
* Every plugin must define a `PLUGIN.toml` containing dependencies and metadata.
* Plugins must fail gracefully if optional external binaries or network connections are unavailable.
* Never hardcode personal paths, credentials, or distribution-specific assumptions in plugin logic.
