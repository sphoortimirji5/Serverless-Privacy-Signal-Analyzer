import boto3
import json
from typing import Any, Dict
from snapshot.interfaces import SnapshotDAO
from auditor.utils import Logger

class BotoSnapshotDAO(SnapshotDAO):
    """Boto3 implementation of SnapshotDAO."""
    
    def __init__(self, ddb_client=None, lambda_client=None):
        self._ddb = ddb_client or boto3.client('dynamodb')
        self._lambda = lambda_client or boto3.client('lambda')

    def export_table(self, table_name: str, bucket_name: str, region: str) -> Dict[str, Any]:
        """Initiates a DynamoDB Export to S3."""
        try:
            # We need the full ARN for the Export API
            # For simplicity, we assume we can construct it or get it from context later.
            # In a real environment, we'd use STS to get account ID.
            account_id = boto3.client('sts').get_caller_identity()['Account']
            table_arn = f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name}"
            
            response = self._ddb.export_table_to_point_in_time(
                TableArn=table_arn,
                S3Bucket=bucket_name,
                S3Prefix="exports/",
                ExportFormat='DYNAMODB_JSON'
            )
            return response
        except Exception as e:
            Logger.log("DAO: Export initiation failed", error=str(e))
            raise e

    def invoke_auditor(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Triggers the Auditor Lambda."""
        try:
            response = self._lambda.invoke(
                FunctionName=function_name,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            return response
        except Exception as e:
            Logger.log("DAO: Auditor invocation failed", error=str(e))
            raise e
