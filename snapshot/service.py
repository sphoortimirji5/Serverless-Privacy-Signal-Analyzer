import os
import boto3
from typing import Optional
from snapshot.interfaces import SnapshotDAO
from auditor.utils import Logger

class SnapshotService:
    """Domain service for managing DynamoDB Batch Snapshots."""
    
    def __init__(self, dao: SnapshotDAO):
        self._dao = dao

    def start_snapshot(self, table_name: str, bucket_name: str, region: str) -> dict:
        """Initiates the daily snapshot process."""
        if not table_name or not bucket_name:
            Logger.log("SnapshotService: Missing configuration", level="ERROR")
            return {"status": "FAILED", "reason": "MISSING_CONFIG"}

        try:
            response = self._dao.export_table(table_name, bucket_name, region)
            export_arn = response['ExportDescription']['ExportArn']
            Logger.log("SnapshotService: Export Started", export_arn=export_arn)
            return {"status": "STARTED", "export_arn": export_arn}
        except Exception as e:
            Logger.log("SnapshotService: Export failed", level="ERROR", error=str(e))
            return {"status": "FAILED", "error": str(e)}

    def handle_export_completion(self, event: dict, auditor_func: str) -> dict:
        """Handles the completion of a snapshot export and triggers the auditor."""
        detail = event.get('detail', {})
        export_arn = detail.get('exportArn')
        status = detail.get('exportStatus')
        
        if status != 'COMPLETED':
            Logger.log("SnapshotService: Non-completed export status received", status=status)
            return {"status": "IGNORED", "reason": f"STATUS_{status}"}
            
        Logger.log("SnapshotService: Export Complete. Triggering Auditor.", export_arn=export_arn)
        
        try:
            self._dao.invoke_auditor(
                function_name=auditor_func,
                payload={"type": "SNAPSHOT_COMPLETE", "export_arn": export_arn}
            )
            return {"status": "AUDIT_TRIGGERED"}
        except Exception as e:
            Logger.log("SnapshotService: Auditor trigger failed", level="ERROR", error=str(e))
            return {"status": "FAILED", "error": str(e)}
