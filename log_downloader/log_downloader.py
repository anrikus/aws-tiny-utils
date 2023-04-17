import pandas as pd
import boto3
from botocore.config import Config
import datetime
import pytz
import toml
from google.api_core.retry import Retry
from dataclasses import dataclass
import json

#  define a custom exception
class StatusRunningException(Exception):
    pass

@dataclass
class QueryConfig:
    log_group: str
    query: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    limit: int = 10000

# Read config

runtime_config = toml.load("runtime_config.toml")

# To get around 'TomlTz' object is not callable
for time_obj in ["start_time", "end_time"]:
    runtime_config[time_obj].replace(tzinfo=pytz.timezone("UTC"))

# Setup
my_config = Config(
    region_name = 'eu-west-1',
)

client = boto3.client(
    'logs', 
    config=Config(
        region_name = runtime_config["region_name"],
    )
)

retry = Retry(
    initial=1.0,
    maximum=10.0,
    multiplier=2,
    predicate=lambda exc: isinstance(exc, StatusRunningException),
)

def start_query(query_config: QueryConfig, client:boto3.client) -> dict:
    """
    Initiates a query. Returns a response object
    """
    response = client.start_query(
    logGroupName=query_config.log_group,
    startTime=int(query_config.start_time.timestamp()),
    endTime=int(query_config.end_time.timestamp()),
    queryString=query_config.query,
    limit=10000
    )

    return response

@retry
def get_query_result(start_query_response: dict, client: boto3.client) -> dict:
    """
    Returns the query results
    """
    response = client.get_query_results(queryId=start_query_response["queryId"])

    if response["status"] == "Running":
        raise StatusRunningException
        
    return response

def main():
    
    query_config = QueryConfig(
        log_group=runtime_config["log_group"],
        query=runtime_config["query"],
        start_time=runtime_config["start_time"],
        end_time=runtime_config["end_time"],
        limit=10000
    )

    complete_response = []
    response = None

    while(True):

        print(f"Querying from {query_config.start_time} to {query_config.end_time}...")

        start_query_response = start_query(query_config, client)
        response = get_query_result(start_query_response, client)
        
        complete_response.extend(response["results"])
        print(f"Found {len(response['results'])} results")
        print(f"First result: {response['results'][0]}")
        print(f"Last result: {response['results'][-1]}")

        # weird off by 1 case
        if len(response["results"])>=10000:
            next_start_time = datetime.datetime.fromisoformat([item["value"] for item in response["results"][-1] if item["field"]==runtime_config["timestamp_field"]][0]).replace(tzinfo=pytz.timezone("UTC"))
            print(f"Next start time: {next_start_time}")
            query_config = QueryConfig(
                log_group=runtime_config["log_group"],
                query=runtime_config["query"],
                start_time=next_start_time,
                end_time=runtime_config["end_time"],
                limit=10000
                )
        else:
            break

    with open(runtime_config["output_file"], 'w') as f:
    # Write the JSON data to the file
        json.dump(complete_response, f)
