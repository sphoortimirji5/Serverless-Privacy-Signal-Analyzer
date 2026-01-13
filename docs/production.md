# Production Operations Guide

## Purpose
The production environment handles real-scale compliance auditing across AWS data lakes. It leverages native AWS services for durability, scalability, and cost-efficiency.

## Architecture Components
- **DynamoDB:** Source of truth for privacy logs (PITR enabled).
- **S3:** Data lake storage for exports and Athena query results.
- **EventBridge:** Orchestrates the transition from Export -> Audit.
- **AWS Lambda:** Lightweight orchestrator for Glue and Athena.
- **AWS Glue:** Automated schema discovery and metadata management.
- **Amazon Athena:** Serverless SQL engine for compliance heuristics.

## Deployment
Deploy the infrastructure using the Serverless Framework:
```bash
# Deploy to dev stage
sls deploy --stage dev

# Deploy to prod stage
sls deploy --stage prod
```

## Monitoring & Observability
- **CloudWatch Insights:** Use structured JSON logs for auditing orchestration steps.
- **Athena Results:** Audit reports are stored in the `AthenaResultsBucket`.
- **Glue Crawler Logs:** Monitor for schema changes or discovery failures.

## Security
- **IAM:** Least-privilege roles defined in `config/${stage}/iam.yml`.
- **Encryption:** S3 buckets use AES256 server-side encryption.
- **Isolation:** Stages (dev/prod) are fully isolated via naming conventions and IAM policies.
