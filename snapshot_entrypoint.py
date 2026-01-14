"""
Batch Snapshot Entrypoint
Role: Thin wrapper for modular SnapshotService.
"""
import os
import boto3
from snapshot.dao import BotoSnapshotDAO
from snapshot.service import SnapshotService

from auditor.utils import tracer, logger, metrics, Logger
import time

def get_service():
    """Dependency injection for SnapshotService."""
    # Note: Clients are lazily initialized in the DAO
    dao = BotoSnapshotDAO()
    return SnapshotService(dao)

@metrics.log_metrics
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def start_snapshot(event, context):
    """Entry point for 1 AM Cron trigger."""
    service = get_service()
    
    table_name = os.environ.get('TABLE_NAME')
    bucket_name = os.environ.get('DATA_LAKE_BUCKET')
    region = boto3.session.Session().region_name or 'us-east-1'
    
    Logger.log("Starting daily DynamoDB export", table=table_name)
    metrics.add_metric(name="ExportInitiated", unit="Count", value=1)
    
    return service.start_snapshot(table_name, bucket_name, region)

@metrics.log_metrics
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def on_export_complete(event, context):
    """Entry point for EventBridge completion trigger."""
    service = get_service()
    
    auditor_func = os.environ.get('AUDITOR_FUNCTION_NAME')
    if not auditor_func:
        # Fallback for local testing/misconfiguration
        auditor_func = "privacy-signal-analyzer-dev-PrivacySignalAuditor"
    
    Logger.log("DynamoDB Export Completed", export_arn=event.get('detail', {}).get('exportArn'))
    metrics.add_metric(name="ExportCompleted", unit="Count", value=1)
        
    return service.handle_export_completion(event, auditor_func)
