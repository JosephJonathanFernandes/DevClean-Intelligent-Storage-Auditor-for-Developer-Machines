# DevClean Manifesto: Why Filesystem-First?

DevClean is built on a specific architectural constraint: **Analyzers must be filesystem-first.** They inspect directories, parse configuration files, and read SQLite databases directly. They do **not** invoke subprocesses like `docker system df` or `conda env list`.

At first glance, this seems counter-intuitive. Why reverse-engineer Docker's storage mechanisms when the Docker CLI exists?

This document outlines the engineering rationale behind this decision and how it shapes DevClean into a predictable, testable, and secure system.

---

## 1. Why Filesystem-First?

### Deterministic
The filesystem is a source of truth. When DevClean analyzes a disk, it observes state directly rather than relying on the output format of a third-party CLI, which may change between versions, respect undocumented environment variables, or fail silently.

### Offline
DevClean does not require a running daemon. It can analyze WSL distributions that are powered off, Docker containers that are stopped, and Python environments that have broken interpreters. A subprocess approach requires the target system to be healthy; a filesystem approach only requires it to exist.

### Testable
Testing a subprocess-based analyzer is notoriously difficult. It requires mocking execution environments or running expensive integration tests. With a filesystem-first approach, we can verify our architecture, domain logic, and detectors using simple directory fixtures and property-based testing.

### Secure
Subprocesses introduce side effects. Running a CLI command can trigger unexpected behaviors (e.g., auto-updates, daemon starts, network requests). By strictly adhering to read-only filesystem traversal during discovery, we guarantee that running a DevClean scan is 100% safe and side-effect free.

### Explainable
When an analyzer finds a target via the filesystem, it inherently knows the exact bytes on disk, the exact paths, and the exact ownership. When a CLI reports "2.4 GB used", it abstracts away the details. DevClean needs those details to provide transparent, explainable recommendations to the user.

### Cross-Platform
Parsing files is cross-platform. Invoking CLI tools introduces platform-specific execution policies, PATH resolution issues, and shell escaping vulnerabilities.

---

## 2. Why Not Subprocesses?

* **Side Effects**: CLIs can mutate state just by being invoked.
* **Permissions**: Subprocesses inherit the caller's environment and permissions. We want DevClean to operate within a strictly confined set of paths defined by an `AllowedRootPolicy`.
* **Latency**: Shelling out to `wsl.exe` or `docker.exe` incurs significant startup latency compared to a direct filesystem `stat()`.
* **Localization**: CLI output varies based on the system locale, making stdout parsing brittle.
* **Version Drift**: Subprocess flags change or deprecate over time. Filesystem structures change too, but they change less frequently and are easier to adapt to gracefully.

---

## 3. The Planning/Execution Separation

By decoupling discovery from execution, DevClean enforces a strict transactional boundary.

1. **Audit (Discovery)**: Detectors observe the filesystem and yield immutable `AuditItem`s. They act purely as facts and do not make judgments.
2. **Recommend (Prescription)**: The `RecommendationEngine` evaluates those facts against deterministic `RecommendationRule`s to produce a `CleanupRecommendation`.
3. **Plan (Orchestration)**: The `CleanupPlanner` matches recommendations against a user-defined `CleanupPolicy` (Conservative, Balanced, Aggressive) to generate a transactional `CleanupPlan`.
4. **Preview (Transparency)**: The `ExplainabilityService` presents the plan transparently to the user, showcasing exact commands, file paths, and potential consequences.
5. **Execute (Safety)**: The `CleanupExecutor` strictly enforces path confinement and performs operations with rollback strategies in mind, securely logging an immutable audit record of actions taken.

This decoupled pipeline guarantees that decisions are deterministic, execution is strictly scoped and safe, and the user's trust is never compromised.
