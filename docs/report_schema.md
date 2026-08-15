# JSON Report Schema Definition

This document defines the structure and stability guarantees of DevClean's machine-readable JSON reports.

## Schema Versioning

All JSON and NDJSON outputs emitted by DevClean, as well as the execution history logs, include versioning metadata at the root level:

```json
{
  "schema_version": "1.0",
  "engine_version": "1.0.0"
}
```

- **`schema_version`**: Governs the structural contract of the JSON document. We adhere strictly to Semantic Versioning for the schema. Any breaking changes to the shape of the data, the removal of fields, or type changes will require a major `schema_version` bump.
- **`engine_version`**: Reflects the version of the DevClean binary that generated the report.

## Field Guarantees & Compatibility Policy

For any `1.x` schema, we guarantee the following:
1. **Additive Changes**: We may add new fields to the root object, summary, or items at any time without a major version bump. Parsers *must* ignore unrecognized fields.
2. **Stable Types**: The data type of an existing field will never change.
3. **Required Fields**: The fields documented below will always be present.

### Root Object
- `schema_version` (string): The version of the JSON schema.
- `engine_version` (string): The version of DevClean.
- `summary` (object): Aggregated statistics about the scan/cleanup.
- `items` (array): A list of discovery or cleanup artifacts.

### Summary Object
- `total_size_bytes` (integer): Total bytes analyzed.
- `reclaimable_bytes` (integer): Bytes that the engine recommends reclaiming.
- `items_scanned` (integer): Total number of discrete items processed.
- `duration_ms` (integer): How long the scan or execution took.

### Item Object
- `id` (string): A UUID representing the artifact.
- `path` (string): The absolute path to the artifact on disk.
- `size_bytes` (integer): The physical size of the artifact.
- `category` (string): The `AuditCategory` enum value (e.g., `python-cache`, `docker-image`).
- `last_accessed_days` (integer): Days since the artifact was last accessed or modified.

## Deprecation Policy

If a field is slated for removal or a major structural change is planned, DevClean will announce the deprecation at least one minor release in advance via `devclean version --verbose` and the GitHub Release Notes. The old schema version will remain selectable via a `--schema` CLI flag during the transition period.
