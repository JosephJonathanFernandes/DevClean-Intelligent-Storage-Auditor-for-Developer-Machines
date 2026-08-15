# Changelog

All notable changes to DevClean will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-15

### Added
- **Filesystem-first architecture**: Deterministic, context-aware analysis of developer artifacts.
- **Explainable recommendations**: Fully decoupled discovery and prescription.
- **Transactional cleanup**: Immutable cleanup plans with `--preview` functionality by default.
- **Plugin system**: Standardized `entry_points` discovery for external Python packages.
- **Automation interfaces**: `--json` and `--ndjson` global support with schema-versioned payloads.
- **Semantic Exit Codes**: Bash-compatible status codes for pipeline integration.
- **Audit Logging**: Local, telemetry-free JSON provenance history of all actions.
- **Diagnostics & Diffing**: `devclean doctor` and `devclean diff` tools for environment health and state drift tracking.
- **Zero Telemetry Guarantee**: `PRIVACY.md` added enforcing completely local, air-gapped security.

### Changed
- Refactored `AnalyzerRegistry` to safely isolate and load third-party extensions.
- Overhauled CLI to act purely as an observer to the Clean Architecture engine.

### Fixed
- Fixed unhandled Typer exceptions polluting semantic exit codes.
- Fixed file permission and size calculation crashes by using strict exception-ignoring traversals.
