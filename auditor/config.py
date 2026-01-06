import os

class AuditConfiguration:
    """
    Handles audit environment parameters and validation.
    
    Rationale:
    While parameters are managed in SSM/Environment variables, this class provides:
    1. Fail-fast Validation: Ensures critical keys exist before execution begins.
    2. Structural Abstraction: Decouples business logic from the source of truth (SSM vs Env vs Secret Manager).
    3. Testability: Allows easy mocking of environment states in local/CI simulations.
    """
    def __init__(self):
        self.crawler_name = os.environ.get('CRAWLER_NAME')
        self.database_name = os.environ.get('DATABASE_NAME')
        self.table_name = os.environ.get('TABLE_NAME')
        self.athena_output = os.environ.get('ATHENA_OUTPUT')

    def is_valid(self):
        return all([self.crawler_name, self.database_name, self.table_name, self.athena_output])
