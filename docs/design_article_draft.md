# Designing a Filesystem-First Cleanup Engine with Clean Architecture and Explainable Recommendations

*Draft article for community publication (e.g., Medium, Dev.to, Python Discord Showcases)*

---

## 1. The Problem
Most disk cleanup utilities operate like black boxes: they scan your drive, find gigabytes of generic "temporary files," and present a massive, terrifying "Delete" button. For everyday consumers, this might be fine. But for developers, a wrong deletion can ruin an entire day. Deleting a critical virtual environment, blowing away active Docker volumes, or purging an undedicated `.git/objects` cache is catastrophic.

I wanted a cleanup tool that felt like a senior engineer pair-programming with me: it should discover facts, explain its reasoning, allow me to inspect the exact consequences, and execute changes predictably.

This led to the creation of **DevClean**, a filesystem-first storage auditing and transactional cleanup engine.

## 2. Why Filesystem-First?
Instead of hardcoding paths to `node_modules` or `~/.cache/pip`, DevClean treats the filesystem as a domain. We built an engine that understands the semantics of developer artifacts. 
A filesystem-first approach means DevClean evaluates artifacts based on access times, project context, and state, rather than just matching file extensions. It allows the system to distinguish between a `node_modules` folder in an actively developed project versus one that hasn't been touched in two years.

## 3. Why Recommendations Were Decoupled
The biggest architectural breakthrough in DevClean was establishing a strict boundary between **Discovery** and **Prescription**. 
In a naïve implementation:
`Detector → AuditItem + Recommendation`

In DevClean's Clean Architecture:
`Detector → AuditItem`
`AuditReport → RecommendationEngine → PrioritizedRecommendation`

Detectors are purely observational—they report *facts* (e.g., "This is a 2GB Python virtual environment last accessed 6 months ago"). The Recommendation Engine then applies context and user-defined policies to decide *what to do* with those facts. 
This decoupling means that DevClean isn't just a cleanup tool; it's a decision-support engine. If we want to add enterprise policies or new AI-assisted heuristics tomorrow, the core detectors don't change at all.

## 4. Transactional Cleanup
Executing deletions on a developer's machine is a high-stakes operation. DevClean uses a **Cleanup Planner** to convert recommendations into immutable `CleanupPlan` objects. 
This provides:
- **Deterministic Previews:** You can see exactly what will happen (`devclean cleanup --preview`) without a single byte changing.
- **Transactional Execution:** The `CleanupExecutor` processes the plan safely, verifying permissions and isolating failures. If a file is locked or a permission is denied, the engine handles it gracefully and logs the exact outcome.
- **Audit Trails:** Every execution generates a provenance log (`history.json`), giving you absolute accountability over what was removed and why.

## 5. Testing Strategy
To guarantee safety, we couldn't rely on unit testing alone. DevClean employs:
- **Property-based testing** using `Hypothesis` to fuzz our core recommendation logic with unpredictable state combinations.
- **Snapshot testing** using `Syrupy` to verify that our `devclean diff` and `devclean report` schemas never break their stable API contracts.
- **Extensive mocking** of the filesystem layer to ensure our engine reacts appropriately to edge cases like symlink loops or suddenly-deleted files.

## 6. Architecture Enforcement
It's easy to start with Clean Architecture, but it's hard to keep it clean. To prevent the presentation layer from leaking into the domain, or infrastructure concerns from polluting our use cases, we integrated `import-linter`. 
Our CI pipeline physically enforces the dependency graph:
`Presentation → Infrastructure → Application → Domain`
If a domain entity accidentally imports a Typer CLI function, the build fails.

## 7. Lessons Learned
Building DevClean taught me that the hardest part of software engineering isn't writing the algorithm—it's defining the contracts. By treating `AuditItem` as an immutable fact and the `CleanupPlan` as a transaction, the rest of the application naturally fell into place. 
DevClean crossed the threshold from a neat utility to a defendable software system the moment the CLI became a pure observer of the engine, rather than its controller.

---
*DevClean v1.0.0 is open-source and available on GitHub. You can install it via `pip install devclean` or explore the architecture at [GitHub URL].*
