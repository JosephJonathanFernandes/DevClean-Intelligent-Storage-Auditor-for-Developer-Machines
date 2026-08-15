# Privacy & Telemetry Guarantees

**DevClean is designed for environments where privacy, security, and IP protection are non-negotiable.** 

We recognize that developer workstations contain highly sensitive proprietary code, credentials, and infrastructure configurations. A storage auditing tool requires deep filesystem access to function, which inherently demands total trust.

To earn and maintain that trust, DevClean adheres to the following strict, unbreakable privacy guarantees:

### 1. Zero Telemetry
**DevClean contains absolutely no telemetry, analytics, or tracking code.** 
We do not track:
- How often you run the tool
- How much space you clean
- What plugins you use
- What errors you encounter

There are no opt-outs because there are no opt-ins. The analytics engine simply does not exist in our codebase.

### 2. Local-Only Analysis
All scanning, detection, recommendation, and planning logic occurs entirely on your local machine. DevClean never uploads metadata, file paths, hashes, or summaries to any external server or API.

### 3. No Network Access During Scans
By default, the core engine and all built-in detectors require **no outbound network access**. You can run DevClean entirely air-gapped without losing any functionality.

*(Note: Third-party plugins that you explicitly choose to install may have their own network requirements. We recommend reviewing the source code of any third-party plugins before running them.)*

### 4. Local-Only Audit Logs
DevClean retains an execution history (`~/.devclean/history.json`) so you can review what actions were taken. This log is stored strictly locally. It is never synchronized, broadcasted, or aggregated.

### 5. Deterministic Transparency
Every action DevClean intends to take can be previewed deterministically before any mutation occurs using `devclean cleanup --preview`. There is no hidden background processing.

## Auditing DevClean
Because DevClean is open-source, we invite security researchers and engineers to audit our codebase. 
If you find any behavior that contradicts these guarantees, please report it immediately as a critical security vulnerability.
