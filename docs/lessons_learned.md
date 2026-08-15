# Lessons Learned: Designing a Filesystem-First Cleanup Engine

Building DevClean to `v1.0.0` was a journey from a simple procedural script to a robust, hexaganol architecture. The goal was straightforward: clean up development artifacts (Docker images, Python virtualenvs, Node modules). The execution, however, demanded significant architectural discipline.

Here are the key engineering lessons learned along the way.

## 1. Why Filesystem-First?

Initially, it's tempting to rely on subprocesses (`docker image ls`, `pip cache dir`, `wsl -l -v`) to find reclaimable space. This approach fails quickly in the real world:
- Subprocesses are slow and fragile.
- Command-line interfaces change their text output formats.
- Environments are heavily customized (e.g., custom Docker daemon paths).

**Lesson:** Treat the filesystem as the source of truth. By reading `ext4.vhdx`, `.whl` files, and `site-packages` directories directly via pure Python, DevClean became deterministic, blazingly fast, and completely isolated from the vagaries of external tool installations.

## 2. Decoupling Discovery from Recommendations

The most pivotal architectural shift was separating "finding things" from "deciding what to do with them."

- **Analyzers** discover immutable *facts* (e.g., "Here is a 5GB Python virtualenv untouched for 90 days"). They return pure domain entities (`AuditItem`).
- The **Recommendation Engine** applies *context and policy* (e.g., "The user is running the 'aggressive' policy and this environment belongs to an archived project. Recommend: DELETE").

**Lesson:** By treating facts as immutable data structures, we enabled a robust plugin system. Third-party developers can write custom `Analyzers` without worrying about user preferences, dry-runs, or execution safety. The system naturally scales horizontally.

## 3. Transactional Cleanup and Dry-Runs by Default

Data destruction is inherently risky. A cleanup utility must earn trust before it mutates the disk.

We introduced the `CleanupPlanner`, which accepts recommendations and outputs an immutable transaction plan. The execution layer processes this plan atomically, catching permission errors and cleanly handling aborts.

**Lesson:** Make safety the default. `devclean cleanup --preview` is the standard behavior. By formalizing operations into a transaction log, we unlocked the ability to provide deep explanations (`devclean explain python-cache`) before a single byte is deleted.

## 4. Architecture Fitness Functions Prevent Regression

When building Clean Architecture, it is incredibly easy for presentation logic (the CLI or progress bars) to leak into the domain.

**Lesson:** Architectural tests are as important as unit tests. We introduced property-based testing and strict dependency linting to ensure our domain layer never imported Typer or Rich. The CLI strictly *observes* the engine via an asynchronous `EventBus`.

## 5. Automation-Friendly Contracts are Product Features

A utility truly matures when it can be integrated into broader workflows without fear of breakage.

During the final push to `v1.0.0`, we implemented:
- Semantic Bash Exit Codes (e.g., Exit Code 3 for "cleanup actions available").
- Strict JSON schema versioning (`schema_version: "1.0"`).
- `devclean diff` to track state drift over time.

**Lesson:** Designing for machines is just as important as designing for humans. A well-defined automation layer transforms a personal utility into an enterprise-ready infrastructure tool.

## Conclusion

DevClean demonstrates that strict software engineering principles—Hexagonal Architecture, Domain-Driven Design, and Systems Programming—are not just for large-scale distributed systems. Applying them to a local utility yields a tool that is maintainable, highly extensible, and above all, safe.
