# DevClean

An intelligent, enterprise-grade storage auditor for developer machines.

## Problem Statement
Over time, developer machines accumulate gigabytes of unused artifacts: orphaned Python virtual environments, massive `node_modules` folders, dangling Docker images, and gigabytes of browser caches. DevClean safely identifies and reclaims this space.

## Features
- Scans for Python, Node.js, Docker, Chrome, and WSL artifacts.
- Plugin-based architecture for easily adding new analyzers.
- Strict Clean Architecture for maintainability and testability.
- Safe-by-default execution: identifies risks associated with each cleanup action.

## Architecture
DevClean follows a strict Hexagonal (Clean) Architecture pattern:
- **Domain:** Core entities and interface protocols (`dataclasses`, no dependencies).
- **Application:** Use cases and orchestration.
- **Infrastructure:** File system access, Docker API integration, configuration.
- **Presentation:** Typer CLI and rich terminal reporting.

*(See `docs/ADR/` for detailed architectural decisions).*

## Installation
*(Coming in later phases)*

## Usage
*(Coming in later phases)*

## Contributing
See `CONTRIBUTING.md` (Coming soon).

## License
MIT
