# Testing Strategy

## Testing Philosophy
Correctness in this system is defined by **structural integrity** (ensuring the orchestration flow completes) and **query accuracy** (ensuring Athena heuristics correctly identify privacy signals). Local tests focus on the former, while production validation handles the latter at scale.

> [!IMPORTANT]
> **Scale Validation:** Local tests cannot validate production scale (e.g., 100K+ records) due to the lack of a real Athena/Glue environment. Production scale is validated via CloudWatch metrics and Athena query execution logs.

## Unit Tests
- **Logic Tested:** Domain-specific logic in `auditor/` and `snapshot/` packages.
- **Expectation:** Deterministic behavior for dependency injection and protocol compliance.
- **Execution:** Handled implicitly by the integration suites.

## Integration Tests
- **Flow:** End-to-end orchestration from `SnapshotStart` -> `ExportComplete` -> `Auditor`.
- **Idempotency:** Verified by simulating multiple export triggers for the same timestamp.
- **Retry Behavior:** Verified using mocked Boto3 clients that return transient errors.
- **Command:** `python3 mock_local_test.py`

## Load / Stress Tests (Local, Best-Effort)
- **Purpose:** Validate system behavior under high concurrency, not raw performance.
- **Tested:** Burst handling of export events, queue growth in the auditor, and backpressure resilience.
- **Explicitly Not Tested:** Network latency, AWS service limits (e.g., Athena DDL limits), or AZ failures.
- **Command:** `python3 mock_stress_test.py`

## Failure Injection
- **Simulation:** Mocked Boto3 clients are configured to raise `ClientError` for specific API calls (e.g., `start_export_table_to_point_in_time`).
- **Expected Response:** Structured JSON logs capturing the error, followed by graceful termination or retry as defined in `utils.py`.

## Production Validation (Out of Scope Locally)
- **Scale & SLOs:** Validated in the AWS environment using CloudWatch Alarms for Lambda durations and Glue Crawler failures.
- **Metrics:**
    - `ExportDuration`: Time from trigger to completion.
    - `AuditSignalCount`: Number of `CRITICAL` signals detected per run.
    - `AthenaQueryScannedBytes`: Cost and performance tracking.
