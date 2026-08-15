# DevClean API Stability & v1.0 Guarantees

DevClean follows strict semantic versioning (SemVer) for its public interfaces. This document outlines what is considered stable in the `v1.x` lifecycle.

## Stable CLI Commands

The following CLI commands and their primary flags are guaranteed not to break backward compatibility in `v1.x`:

- `devclean scan`
  - `--json`, `--ndjson`
- `devclean cleanup`
  - `--preview`, `--policy`, `--json`, `--ndjson`
- `devclean report`
  - `--html`, `--json`
- `devclean history`
  - `--json`
- `devclean explain`
- `devclean diff`
- `devclean doctor`

**Exit Codes:**
The semantic exit codes defined in `ExitCode` are stable:
- `0` (Success)
- `1` (Execution Failure)
- `2` (Validation/Config Failure)
- `3` (Cleanup Actions Available - only emitted by `cleanup --preview`)
- `4` (Permission Required)

## Stable JSON Schema

The `v1.0` JSON schema emitted by `devclean report --json` and `devclean scan --json` is considered a stable API. Scripts and automation tools can reliably parse:
- `schema_version`: Currently `"1.0"`.
- `summary`: Contains `total_size_bytes`, `total_files`, `risk_distribution`.
- `items`: The array of discovered `AuditItem` facts.
- `recommendations`: The array of cleanup actions proposed by the policy engine.

Changes to this schema will result in a `schema_version` increment.

## Stable Plugin Interface

The base class `devclean.domain.services.analyzer.Analyzer` and the `AnalyzerRegistry` entry point group (`devclean.analyzers`) are stable. External analyzers adhering to this contract will remain compatible through all `v1.x` releases.

## Deprecation Policy

If a feature, command, or schema element is targeted for removal:
1. It will be marked as deprecated in a minor release (e.g., `v1.1.0`) with a visible console warning.
2. It will remain fully functional for at least one full minor release cycle.
3. It will only be removed in the next major version (`v2.0.0`).
