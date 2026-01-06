import os

# Mock environment initialization (MUST be before imports that initialize boto3)
os.environ["SLS_STAGE"] = "dev"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

import json
import unittest
from unittest.mock import MagicMock, patch
from snapshot_entrypoint import start_snapshot, on_export_complete
from privacy_auditor import lambda_handler

# Mock environment initialization
os.environ["SLS_STAGE"] = "dev"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["TABLE_NAME"] = "mock_table"
os.environ["DATA_LAKE_BUCKET"] = "mock-bucket"
os.environ["CRAWLER_NAME"] = "mock-crawler"
os.environ["DATABASE_NAME"] = "mock_db"
os.environ["ATHENA_OUTPUT"] = "s3://mock-results/results/"
os.environ["AUDITOR_FUNCTION_NAME"] = "MockAuditorFunction"

class TestSweepArchitecture(unittest.TestCase):

    @patch('boto3.session.Session')
    @patch('boto3.client')
    def test_full_snapshot_flow(self, mock_boto, mock_session):
        """Tests the sequence from 1AM Cron to Audit Completion."""
        
        # 0. Mock Session Region
        mock_session.return_value.region_name = "us-east-1"
        
        # 1. Setup Service Mocks
        mock_sts = MagicMock()
        mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_ddb = MagicMock()
        mock_lambda = MagicMock()
        mock_glue = MagicMock()
        mock_athena = MagicMock()

        def side_effect(service_name, **kwargs):
            if service_name == 'dynamodb': return mock_ddb
            if service_name == 'lambda': return mock_lambda
            if service_name == 'glue': return mock_glue
            if service_name == 'athena': return mock_athena
            if service_name == 'sts': return mock_sts
            return MagicMock()

        mock_boto.side_effect = side_effect

        mock_context = MagicMock()
        mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:mock"
        mock_context.aws_request_id = "mock-req-id-123"

        # --- Phase 1: Start Snapshot (1 AM Cron) ---
        print("\nPhase 1: Triggering 1 AM Snapshot Start...")
        mock_ddb.export_table_to_point_in_time.return_value = {
            'ExportDescription': {'ExportArn': 'arn:aws:dynamodb:export:123'}
        }
        
        start_res = start_snapshot({}, mock_context)
        print(f"Start Snapshot Result: {start_res}")
        self.assertEqual(start_res['status'], 'STARTED')
        mock_ddb.export_table_to_point_in_time.assert_called_once()

        # --- Phase 2: Export Completion (EventBridge) ---
        print("\nPhase 2: Handling Export Completion...")
        eb_event = {
            "detail": {
                "exportArn": "arn:aws:dynamodb:export:123",
                "exportStatus": "COMPLETED"
            }
        }
        
        complete_res = on_export_complete(eb_event, mock_context)
        print(f"Completion Result: {complete_res}")
        self.assertEqual(complete_res['status'], 'AUDIT_TRIGGERED')
        mock_lambda.invoke.assert_called_once()

        # --- Phase 3: Audit Execution ---
        print("\nPhase 3: Executing Auditor logic...")
        mock_glue.get_crawler.return_value = {'Crawler': {'State': 'READY'}}
        mock_athena.start_query_execution.return_value = {'QueryExecutionId': 'q-123'}
        mock_athena.get_query_execution.return_value = {'QueryExecution': {'Status': {'State': 'SUCCEEDED'}}}

        # Simulate the Auditor being triggered by the payload sent in Phase 2
        audit_event = {"type": "SNAPSHOT_COMPLETE"}
        audit_res = lambda_handler(audit_event, mock_context)
        print(f"Audit Result: {audit_res}")
        
        self.assertEqual(audit_res['statusCode'], 200)
        self.assertEqual(audit_res['status'], 'COMPLETED')
        
        mock_glue.start_crawler.assert_called_once()
        mock_athena.start_query_execution.assert_called_once()

        print("\nSUCCESS: Batch Snapshot orchestration verified.")

if __name__ == "__main__":
    unittest.main()
