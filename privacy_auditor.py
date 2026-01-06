"""
Privacy Signal Auditor - Enterprise Orchestration Core
Role: Orchestrates multi-stage privacy audits by coordinating AWS Glue and Amazon Athena.
Design Pattern: SOLID Principles (SRP, OCP, LSP, ISP, DIP).
"""

import boto3
from botocore.config import Config

from auditor.utils import Logger
from auditor.config import AuditConfiguration
from auditor.discovery import GlueDAO, GlueDiscoveryService
from auditor.analytics import AthenaDAO, AthenaAnalyticsService
from auditor.orchestrator import ComplianceAuditOrchestrator

# Adaptive retry configuration for high-throughput resilience.
BOTO_CONFIG = Config(
    retries={'mode': 'adaptive', 'max_attempts': 10}
)

def lambda_handler(event, context):
    """Entry point for AWS Lambda, responsible for DI and high-level execution."""
    Logger.log("Audit execution started", request_id=context.aws_request_id)

    config = AuditConfiguration()
    if not config.is_valid():
        Logger.log("Environment configuration error: MISSING_RESOURCES", level="ERROR")
        return {'statusCode': 500, 'body': 'Internal Configuration Error'}

    # Dependency Injection Layer 1: DAOs (Direct AWS SDK Interactions)
    glue_dao = GlueDAO(boto3.client('glue', config=BOTO_CONFIG))
    athena_dao = AthenaDAO(boto3.client('athena', config=BOTO_CONFIG))

    # Dependency Injection Layer 2: Services (Execution of Domain Operations)
    discovery_service = GlueDiscoveryService(glue_dao, config.crawler_name)
    analytics_service = AthenaAnalyticsService(athena_dao)
    
    # Dependency Injection Layer 3: Orchestrator (Workflow Management)
    orchestrator = ComplianceAuditOrchestrator(discovery_service, analytics_service)

    try:
        query_id, status = orchestrator.run_opt_out_audit(config)
        
        if status == 'SUCCEEDED':
            Logger.log("Privacy Audit Successful", query_id=query_id)
            return {'statusCode': 200, 'query_id': query_id, 'status': 'COMPLETED'}

        else:
            Logger.log("Privacy Audit Failed", level="ERROR", query_id=query_id, status=status)
            return {'statusCode': 500, 'query_id': query_id, 'status': status}

    except Exception as e:
        Logger.log("Critical failure in audit orchestration", level="ERROR", error=str(e))
        return {'statusCode': 500, 'body': 'Audit Execution Failed'}
