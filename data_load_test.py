"""
DynamoDB Volume Load Testing Utility
Benchmarks Data Catalog discovery and Athena performance by ingesting large record volumes.
"""

import boto3
import time
import argparse
import random
import uuid
import os

def create_mock_record():
    """
    Generates a realistic synthetic privacy signal record for high-volume testing.
    """
    return {
        'user_id': {'S': str(uuid.uuid4())},
        'timestamp': {'S': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
        'action': {'S': random.choice(['opt_in', 'opt_out', 'preference_update'])},
        'source': {'S': 'mission_critical_load_test'},
        'is_mock': {'BOOL': True}
    }

def load_data(table_name, count):
    """
    Executes a high-volume batch write operation to the target DynamoDB table.
    """
    print(f"--- Data Load Started ---")
    print(f"Table: {table_name}")
    print(f"Count: {count}")
    
    dynamodb = boto3.client('dynamodb')
    batch_size = 25 # Maximum allowed by AWS DynamoDB BatchWriteItem
    loaded = 0
    start_time = time.time()

    for i in range(0, count, batch_size):
        request_items = []
        for _ in range(min(batch_size, count - loaded)):
            request_items.append({'PutRequest': {'Item': create_mock_record()}})
        
        try:
            dynamodb.batch_write_item(RequestItems={table_name: request_items})
            loaded += len(request_items)
            if loaded % 100 == 0:
                print(f"Success: Ingested {loaded}/{count} records...")
        except Exception as e:
            print(f"CRITICAL ERROR: Batch write failure: {str(e)}")
            break

    total_time = time.time() - start_time
    print(f"\nLoad Test Completed!")
    print(f"Final Count: {loaded} records")
    print(f"Duration: {total_time:.2f}s")
    print(f"Throughput: {loaded / total_time:.2f} items/sec")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DynamoDB Data Loading Utility")
    parser.add_argument("--table", default="privacy-signal-analyzer-logs-dev", help="Target DynamoDB Table Name")
    parser.add_argument("--count", type=int, default=1000, help="Total synthetic record count")
    
    args = parser.parse_args()
    load_data(args.table, args.count)
