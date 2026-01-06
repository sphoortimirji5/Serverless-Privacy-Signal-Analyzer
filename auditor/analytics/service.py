from .interfaces import AbstractQueryDAO
from ..utils import Poller

class AthenaAnalyticsService:
    """High-level Orchestration for Athena Query Execution."""
    def __init__(self, dao: AbstractQueryDAO):
        self.dao = dao

    def run_query(self, query: str, database: str, output: str) -> str:
        return self.dao.start_execution(query, database, output)

    def wait_completion(self, query_id: str) -> str:
        return Poller.wait(
            f"Query {query_id}",
            lambda: self.dao.fetch_execution_state(query_id),
            success_states=['SUCCEEDED'],
            failure_states=['FAILED', 'CANCELLED']
        )
