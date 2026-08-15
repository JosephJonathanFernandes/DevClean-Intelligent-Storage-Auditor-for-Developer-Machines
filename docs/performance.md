# DevClean Performance & Benchmarks

DevClean is engineered with a strict performance envelope. We maintain a manual benchmark policy to avoid flaky CI results while ensuring the application scales to massive developer filesystems.

## Benchmark Methodology

The primary metric for DevClean's efficiency is the synthetic filesystem benchmark, which simulates a heavily populated developer workstation.

### Hardware Context
- **CPU**: Modern x86_64 / ARM64 (Multi-core)
- **Disk**: NVMe SSD (typical developer setup)
- **Memory**: 16GB+ RAM

### Synthetic Workload Configuration
- **Filesystem Size**: 50,000+ files and directories.
- **Complexity**: Deep nesting, mimicking `node_modules`, `.git`, Python `venv`s, and Docker overlay caches.
- **Analyzers Loaded**: 4 Built-in (Python, Chrome, Docker, WSL) + variable external plugins.

### Performance Results

In our standardized benchmark runs, DevClean achieves:

- **Scan Time**: ~36 ms for the full synthetic workload.
- **Startup Time**: < 100 ms to full operational readiness (plugin loading, config parsing).
- **Memory Footprint**: Extremely low overhead. `AuditItem` entities are tightly packed immutable dataclasses, allowing millions of entries without memory exhaustion.

### Why It's Fast

1. **Filesystem-First Approach**: Rather than invoking heavy subprocesses (e.g., `docker system df` or `wsl.exe`), analyzers directly parse the filesystem artifacts where possible.
2. **Immutable Domain Entities**: Zero tracking overhead. Once an `AuditItem` is created, it never mutates.
3. **Event-Driven Architecture**: The `EventBus` prevents blocking during directory traversal and UI updates.
4. **Targeted Exclusions**: The configuration engine naturally prunes expensive paths (like `.git`) entirely.
