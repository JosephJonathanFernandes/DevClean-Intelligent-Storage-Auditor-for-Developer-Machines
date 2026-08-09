# Testing Philosophy and Harness

DevClean maintains an extremely strict testing philosophy to ensure it behaves predictably and safely on developer machines.

## 1. Filesystem-First Purity
All analyzers must implement a read-only, filesystem-first detection strategy. We do not invoke subprocesses (`docker`, `wsl.exe`, etc.) during standard scans because they can introduce side effects, block, or mutate state. 
This purity is enforced through `PlatformServices`, which abstracts the filesystem, clock, and environment.

## 2. Property-Based Testing
We use `hypothesis` to test the outer bounds of our aggregation logic. For example, we simulate generating thousands of random `AuditItem`s across various sizes and categories to guarantee that our `ScanSummary` aggregation logic never breaks.

## 3. Snapshot Testing
Using `syrupy`, we capture full `ScanResult` JSON structures and lock them as golden snapshots. Any change to the detection logic, metadata schema, or aggregation will immediately fail the snapshot test, ensuring we don't accidentally drop fields or change risk categorizations.

## 4. Architecture Enforcement
We use fitness functions (via `import-linter`) to enforce Clean Architecture.
- `domain` cannot import `application` or `infrastructure`.
- `application` cannot import `infrastructure`.

## 5. Analyzer Contracts
Every analyzer must pass the `AnalyzerContractTestSuite`. This ensures:
- **No side effects**: It does not mutate the `PlatformServices` filesystem.
- **Deterministic ordering**: Yields items sorted by `(category, path, size)`.
- **Explainability**: Every reclaimable item has a `Recommendation`.
