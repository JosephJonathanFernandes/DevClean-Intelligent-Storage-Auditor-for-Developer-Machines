# ADR 0003: Plugin-Based Analyzers

## Status
Accepted

## Context
DevClean needs to scan for many different types of developer artifacts (Python virtual environments, Node modules, Docker images, Chrome profiles, etc.). Hardcoding these scans into a monolithic process would result in an unmaintainable, brittle God class.

## Decision
We will define an `Analyzer` Protocol in the domain layer. Every specific analyzer (e.g., `PythonAnalyzer`, `DockerAnalyzer`) will implement this protocol. An `AnalyzerRegistry` or standard use case orchestrator will dynamically discover and execute these plugins.

## Consequences
**Pros:**
* **Extensibility:** New analyzers can be added simply by creating a new class that implements the `Analyzer` protocol, without touching the core scanning engine.
* **Separation of Concerns:** Each analyzer is only responsible for its specific domain (e.g., the Python analyzer only knows about `pip` caches and virtual environments).
* **Testability:** Individual analyzers can be unit tested in isolation.

**Cons:**
* Requires an orchestration mechanism to run all analyzers and aggregate their results into a single `AuditReport`.
