# DevClean

An intelligent, enterprise-grade storage auditor for developer machines.

## Problem Statement
Over time, developer machines accumulate gigabytes of unused artifacts: orphaned Python virtual environments, massive `node_modules` folders, dangling Docker images, and gigabytes of browser caches. DevClean safely identifies and reclaims this space.

## Features
- **Filesystem-First**: Scans for Python, Docker, Chrome, and WSL artifacts using deterministic, read-only file inspections without relying on third-party CLIs.
- **Deep Decoupling**: Separation of Discovery (Detectors) from Prescription (Recommendation Engine). Policy never mixes with fact.
- **Transactional Execution**: Analyzes disks efficiently and prepares an execution `CleanupPlan` with explicit previews and `RollbackStrategy` definitions.
- **Safe-by-Default**: Every discovered item receives a strict safety risk classification (`SAFE`, `LOW`, `MODERATE`, `HIGH`) and must pass a `CleanupPolicy` before execution. Path confinement explicitly prevents rogue deletions.
- **Enterprise Testing**: Robust test suite including analyzer contract testing, mutation-safety verification, idempotency tests, snapshot tests, and property-based validations via Hypothesis.

## Architecture
DevClean follows a strict Hexagonal (Clean) Architecture pattern:
- **Domain:** Core entities, interfaces, and Enums (`dataclasses` and protocols, no dependencies).
- **Application:** The `RecommendationEngine`, `CleanupPlanner`, and `ExplainabilityService` orchestrate the business logic.
- **Infrastructure:** Filesystem detectors, operation executors, logging, configuration, and environment abstraction.
- **Presentation:** (WIP) Typer CLI and rich terminal reporting.

*(See `docs/filesystem_first.md` for our philosophy and rationale).*

## Installation
*(Coming in Phase 7)*

## Usage
*(Coming in Phase 7)*

## Development

```bash
# Setup
poetry install

# Formatting and Type-checking
ruff check .
ruff format .
mypy src

# Architecture Enforcement
lint-imports

# Testing
pytest tests -vv
```

## Contributing
See `CONTRIBUTING.md` (Coming soon).

## License
MIT
