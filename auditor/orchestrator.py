from .discovery import AbstractGlueDiscoveryService
from .analytics import AbstractAthenaAnalyticsService
from .config import AuditConfiguration
from .utils import Logger

class ComplianceAuditOrchestrator:
    """Coordinates the compliance audit workflow using abstract Glue and Athena services."""
    def __init__(self, discovery_service: AbstractGlueDiscoveryService, analytics_service: AbstractAthenaAnalyticsService):
        self.discovery_service = discovery_service
        self.analytics_service = analytics_service

    def run_opt_out_audit(self, config: AuditConfiguration):
        """Executes a definitive opt-out audit analytics workflow."""
        Logger.log("Starting Audit: Discovery Phase")
        
        # 1. Trigger Discovery (S3 Catalog Update)
        self.discovery_service.refresh()
        self.discovery_service.wait_ready()

        Logger.log("Starting Audit: Analysis Phase")

        # 2. Execute Analysis (Athena Analysis)
        query = f'SELECT count(*) as total_opt_outs FROM "{config.database_name}"."{config.table_name}" WHERE action = \'opt_out\';'
        query_id = self.analytics_service.run_query(query, config.database_name, config.athena_output)
        
        status = self.analytics_service.wait_completion(query_id)
        return query_id, status

