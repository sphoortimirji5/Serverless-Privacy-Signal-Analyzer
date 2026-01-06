"""
Logic-Level Mock Stress Test (Snapshot Architecture)
Simulates concurrent Audit triggers to verify Auditor thread-safety and orchestration logic.
"""

import concurrent.futures
import time
import json
import os
from unittest.mock import MagicMock, patch
from privacy_auditor import lambda_handler

# Mock environment initialization
os.environ["SLS_STAGE"] = "dev"
os.environ["CRAWLER_NAME"] = "mock-crawler"
os.environ["DATABASE_NAME"] = "mock_db"
os.environ["TABLE_NAME"] = "mock_table"
os.environ["ATHENA_OUTPUT"] = "s3://mock-results/results/"
os.environ["DATA_LAKE_BUCKET"] = "mock-lake"

def simulate_audit(audit_id):
    """Simulates a concurrent Privacy Audit trigger."""
    with patch('boto3.client') as mock_boto:
        # Each thread gets its own mock set
        mock_glue = MagicMock()
        mock_athena = MagicMock()
        
        def side_effect(service_name, **kwargs):
            if service_name == 'glue': return mock_glue
            if service_name == 'athena': return mock_athena
            return MagicMock()
            
        mock_boto.side_effect = side_effect
        
        # Mock Glue/Athena Responses
        mock_glue.get_crawler.return_value = {'Crawler': {'State': 'READY'}}
        mock_athena.start_query_execution.return_value = {'QueryExecutionId': f'q-{audit_id}'}
        mock_athena.get_query_execution.return_value = {'QueryExecution': {'Status': {'State': 'SUCCEEDED'}}}
        
        mock_context = MagicMock()
        mock_context.aws_request_id = f"req-{audit_id}"
        
        start = time.time()
        try:
            # Simulate trigger from Snapshot Completion
            event = {"type": "SNAPSHOT_COMPLETE", "export_arn": f"arn:aws:export:{audit_id}"}
            resp = lambda_handler(event, mock_context)
            return {"id": audit_id, "success": resp['statusCode'] == 200, "latency": time.time() - start}
        except Exception as e:
            return {"id": audit_id, "success": False, "error": str(e), "latency": time.time() - start}

def run_mock_stress_test(total_audits=20, concurrency=8):
    print(f"--- Starting Auditor Stress Test (Snapshot Architecture) ---")
    print(f"Total Concurrent Audits: {total_audits}")
    print(f"Worker Threads: {concurrency}")
    
    results = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(simulate_audit, i) for i in range(total_audits)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    total_duration = time.time() - start_time
    success_count = sum(1 for r in results if r['success'])
    avg_latency = sum(r['latency'] for r in results) / total_audits
    
    print("\n--- Auditor Stress Test Analytics ---")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Average Audit Latency: {avg_latency:.4f}s")
    print(f"Audit Throughput: {total_audits / total_duration:.2f} audits/sec")
    print(f"Audit Success Rate: {(success_count / total_audits) * 100:.2f}%")
    
    if success_count == total_audits:
        print("\nVERIFIED: Auditor orchestration is stable under concurrent triggers.")
    else:
        print(f"\nFAILED: {total_audits - success_count} audits encountered logic errors.")
        exit(1)

if __name__ == "__main__":
    run_mock_stress_test()
