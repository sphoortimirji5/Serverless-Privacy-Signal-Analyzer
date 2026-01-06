from .interfaces import AbstractMetadataDAO
from ..utils import Poller

class GlueDiscoveryService:
    """High-level Orchestration for Glue Metadata Discovery."""
    def __init__(self, dao: AbstractMetadataDAO, crawler_name: str):
        self.dao = dao
        self.crawler_name = crawler_name

    def refresh(self):
        self.dao.trigger_crawler(self.crawler_name)

    def wait_ready(self):
        return Poller.wait(
            f"Crawler {self.crawler_name}",
            lambda: self.dao.fetch_crawler_state(self.crawler_name),
            success_states=['READY'],
            initial_delay=10,
            max_delay=60
        )
