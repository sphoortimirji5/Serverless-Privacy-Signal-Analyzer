# Migration Strategy: Environments & Evolution

## Purpose
This guide outlines the strategy for migrating between infrastructure environments (e.g., Dev to Prod) and evolving system components (e.g., Lambda to Fargate) while ensuring **zero data loss** and **zero service interruption**.

## 1. Environment Migration (Dev → Prod)
The system uses a stage-isolated architecture to ensure that migrations between environments do not impact data integrity or service availability.

### Data Integrity Strategy
- **DynamoDB PITR:** Point-in-Time Recovery is enabled on all production tables, allowing for recovery to any second in the last 35 days.
- **S3 Versioning:** Data lake buckets use versioning to prevent accidental deletions or overwrites during migration cycles.
- **Isolated State:** Each environment (`dev`, `prod`) maintains its own S3 buckets and DynamoDB tables, preventing cross-environment data contamination.

### Service Continuity
- **Blue/Green Deployments:** The Serverless Framework handles atomic updates to Lambda functions. Traffic is only shifted once the new version is successfully provisioned.
- **Asynchronous Decoupling:** Since the audit process is triggered by EventBridge events, environment updates do not interrupt the transactional flow in DynamoDB.

## 2. Component Evolution (Lambda → Fargate)
As data volumes scale, the system supports evolving from Lambda-based orchestration to ECS Fargate without downtime. This is achieved through **Event-Driven Decoupling** and **Shared Logic Cores**.

### The "How": Technical Mechanism
1. **EventBridge Multi-Targeting:** Amazon EventBridge allows a single rule (e.g., `ExportComplete`) to have up to 5 targets. During evolution, a new target (AWS Step Functions or ECS Task) is added to the existing rule alongside the Lambda Auditor.
2. **Shared Logic Core:** The core business logic resides in the `auditor/` package, which is decoupled from the execution environment via Python Protocols. This same package can be executed as a Lambda handler or as a containerized CLI tool in Fargate.
3. **Shadow Mode Validation:** Both the Lambda and Fargate components receive the same event payload. They execute the same audit logic against the same S3 snapshot. Results are written to unique, versioned S3 paths for comparison.
4. **Atomic Cutover:** Once the Fargate implementation is verified, the Lambda target is removed from the EventBridge rule. This is a metadata-only change in the AWS control plane, occurring in milliseconds without interrupting the data pipeline.

### Data Persistence during Evolution
- **Stateless Orchestration:** The Auditor logic is stateless; it reads from S3 snapshots and writes to Athena. This allows for seamless switching between execution environments without state migration.
- **Idempotent Triggers:** Both Lambda and Fargate implementations use the same idempotency logic (checking export status), ensuring that a single snapshot is never processed twice.

## 3. Rollback Strategy
- **Infrastructure as Code:** All environment states are defined in `serverless.yml`. Rollbacks are performed via `sls rollback`, which restores the previous CloudFormation stack state and Lambda versions instantly.
- **Data Snapshots:** In the event of a logic failure during migration, audits can be re-run against the existing S3 snapshots, ensuring no loss of compliance visibility.
