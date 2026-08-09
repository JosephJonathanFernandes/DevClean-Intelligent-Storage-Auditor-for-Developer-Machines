# ADR 0002: Clean Architecture Boundaries

## Status
Accepted

## Context
DevClean requires an architecture that can scale as we add more complex analyzers, varying cleanup strategies, and diverse reporting formats (terminal, JSON, HTML). A flat directory structure or a traditional layered structure without strict boundary enforcement could lead to spaghetti code and tight coupling.

## Decision
We will adopt a Hexagonal/Clean Architecture approach with strict layer separation:
* `domain/`: Entities, enums, value objects, and interface protocols (Services, Repositories). Has no dependencies.
* `application/`: Use cases, orchestrators, and concrete implementations of domain services (like Analyzers). Depends only on `domain`.
* `infrastructure/`: Implementations of I/O, file system access, Docker APIs, and configuration. Depends on `application` and `domain`.
* `presentation/`: Typer CLI and formatters. Depends on `application`.

## Consequences
**Pros:**
* **Maintainability:** Changes in external systems (e.g., Docker CLI changes) only affect the `infrastructure` layer.
* **Flexibility:** Easy to swap out reporting formats or add a REST API in the future without changing core logic.
* **Testability:** The application and domain layers can be thoroughly tested using in-memory mock repositories and fake filesystems.

**Cons:**
* **Boilerplate:** Requires defining explicit interfaces (Protocols) and mapping data between layers.
