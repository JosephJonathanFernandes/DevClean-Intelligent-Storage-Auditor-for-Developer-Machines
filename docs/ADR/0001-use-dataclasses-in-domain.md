# ADR 0001: Use Dataclasses in Domain Layer

## Status
Accepted

## Context
When modeling the core domain of DevClean (entities like `AuditItem`, `AuditReport`, and `ScanSummary`), we needed to decide on a data container technology. The main candidates were standard library `dataclasses` and third-party libraries like `pydantic`.

While Pydantic offers powerful runtime validation and serialization, using it in the core domain layer introduces a dependency on a third-party framework.

## Decision
We will use standard Python `dataclasses` (specifically `frozen=True` where appropriate for value objects and aggregates) for the core domain layer. Pydantic will be reserved exclusively for the infrastructure (configuration) and presentation (CLI parsing/serialization) layers.

## Consequences
**Pros:**
* **Zero Dependencies:** The domain layer remains pure and free of third-party framework leakage.
* **Testability:** Core business logic is isolated and easier to unit test without mocking framework specifics.
* **Adherence to Clean Architecture:** The domain is the center of the application and should depend on nothing else.

**Cons:**
* Runtime validation must be handled manually or pushed to the application/presentation boundaries.
