# 4. Filesystem-First Analyzers

Date: 2026-08-09

## Status
Accepted

## Context
DevClean aims to be a high-speed, deterministic, and safe audit engine. During the design of complex analyzers like Docker and WSL, we encountered a choice:
1. Invoke sub-processes (e.g. `docker system df` or `wsl.exe -l -v`) to get pristine information.
2. Rely entirely on filesystem heuristics (e.g. inspecting `%LOCALAPPDATA%\Docker\wsl\data\ext4.vhdx`).

Subprocesses introduce significant latency, context-switching overhead, platform-specific variability, potential deadlocks, and mutation risks (some CLI commands implicitly alter state or start daemons). 

## Decision
We will adhere to a **Filesystem-First Analysis Pattern**:
1. Analyzers are fundamentally **read-only**.
2. Analyzers **do not** invoke subprocesses during standard execution.
3. Filesystem inspection is the primary detection mechanism.
4. If external tooling is required for deeper insights in the future, it must be introduced as an optional enrichment layer (via abstract Provider interfaces in the domain) rather than being hardcoded into the analyzer loop.

## Consequences
- **Positive**: Complete determinism, fast execution, cross-platform stability, and absolute confidence in side-effect-free execution.
- **Negative**: We must rely on heuristics (like scanning `ext4.vhdx` files) rather than official CLI outputs, which requires reverse-engineering standard storage patterns for tools like Docker Desktop and WSL.
