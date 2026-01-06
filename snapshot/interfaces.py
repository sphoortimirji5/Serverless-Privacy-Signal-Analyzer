from typing import Protocol, Any, Dict

class SnapshotDAO(Protocol):
    """Protocol for Snapshot Data Access Object."""
    
    def export_table(self, table_name: str, bucket_name: str, region: str) -> Dict[str, Any]:
        """Initiates a DynamoDB Export to S3."""
        ...

    def invoke_auditor(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Triggers the Auditor Lambda."""
        ...
