from botocore.exceptions import ClientError
from ..utils import Logger

class GlueDAO:
    """AWS Glue Implementation of Metadata DAO."""
    def __init__(self, glue_client):
        self.client = glue_client

    def trigger_crawler(self, name: str):
        try:
            self.client.start_crawler(Name=name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'CrawlerRunningException':
                Logger.log("Crawler already running", crawler=name)
            else:
                raise

    def fetch_crawler_state(self, name: str) -> str:
        response = self.client.get_crawler(Name=name)
        return response['Crawler']['State']
