# Observability, Metrics & SLAs

This document outlines the observability architecture for the Serverless Privacy Signal Analyzer, including how to monitor system health, performance, and SLAs in production.

## 1. Architectural Overview
We use **AWS Lambda Powertools** as the core telemetry engine to provide high-fidelity insights with minimal latency impact.

| Feature | Production (AWS) | Local (Your Machine) |
| :--- | :--- | :--- |
| **JSON Logs** | Captured by CloudWatch / Datadog | Printed to Terminal/Stdout |
| **Custom Metrics** | Automatically indexed by CloudWatch EMF | Shown as JSON blocks in terminal |
| **Distributed Tracing** | Active (Trace IDs visible in X-Ray) | Gracefully disabled (No errors) |

## 2. Production vs. Local Philosophy
We use a **"Write Once, Observe Anywhere"** strategy. The code emits the same telemetry regardless of where it runs, but the infrastructure handles it differently:

- **In Production**: AWS Lambda captures `stdout`. CloudWatch index the logs and metrics. If Datadog is configured (via Lambda Extension or Log Forwarder), it automatically ingests these same JSON logs and EMF metrics for high-level dashboarding.
- **In Local/LocalStack**: The same JSON structures are printed to your terminal. This ensures that your local environment is a "true-to-production" mirror of what will be logged in the cloud, allowing you to catch telemetry bugs before deployment.

## 2. Service Level Indicators (SLIs)
The following metrics are emitted automatically and should be used to define CloudWatch Alarms for your SLAs.

### Privacy Audit Orchestration
- `AuditDuration`: Time taken from start to finish of a compliance audit.
- `AuditSuccess`: Count of successfully completed queries.
- `AuditFailure`: Count of queries that failed logic checks or service calls.
- `AuditCriticalFailure`: Count of unhandled exceptions in the orchestrator.

### Snapshot & Ingestion
- `ExportInitiated`: Triggers from the 1 AM Cron job.
- `ExportCompleted`: Triggers on EventBridge completion event.

## 3. Querying Logs
Because all logs are structured JSON, you can use **CloudWatch Logs Insights** to perform powerful queries.

**Example: Average Audit Duration by Stage**
```sql
fields @timestamp, duration
| filter message = "Privacy Audit Successful"
| stats avg(duration) by stage
| sort @timestamp desc
```

**Example: Error Rate Analysis**
```sql
fields @timestamp, level, message, error
| filter level = "ERROR"
| stats count(*) by message
```

## 4. Distributed Tracing
X-Ray is enabled for all Lambda functions. You can view the service map in the AWS Console to see:
- Interaction between `SnapshotStart` and DynamoDB.
- `SnapshotCompletionHandler` triggering the `PrivacySignalAuditor`.
- Orchestrator calls to Glue Crawlers and Athena Query Execution.

## 5. Local Development
When running locally (e.g., via `mock_local_test.py`), the observability layer automatically degrades gracefully:
- **Logger**: Defaults to standard `stdout` (still JSON formatted).
- **Metrics**: Prints the EMF JSON structure to console.
- **Tracer**: Disables segment emission to avoid `ConnectionError`.


> To view simplified logs during local development, use a JSON formatter like `python3 mock_local_test.py | jq`.
