class AthenaDAO:
    """AWS Athena Implementation of Query DAO."""
    def __init__(self, athena_client):
        self.client = athena_client

    def start_execution(self, query: str, database: str, output: str) -> str:
        response = self.client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': output}
        )
        return response['QueryExecutionId']

    def fetch_execution_state(self, query_id: str) -> str:
        response = self.client.get_query_execution(QueryExecutionId=query_id)
        return response['QueryExecution']['Status']['State']
