import os
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from aws_costs import ddb_write_cost, money
from sample_jobs import SAMPLE_JOB_REQUESTS


TABLE_NAME = "db_batch_window_requests"
REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


def get_table(dynamodb):
    return dynamodb.Table(TABLE_NAME)


def create_table_if_needed(dynamodb):
    existing_tables = dynamodb.meta.client.list_tables()["TableNames"]
    if TABLE_NAME in existing_tables:
        print(f"Table already exists: {TABLE_NAME}")
        return get_table(dynamodb)

    print(f"Creating table: {TABLE_NAME}")
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "batch_date", "KeyType": "HASH"},
            {"AttributeName": "window_job_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "batch_date", "AttributeType": "S"},
            {"AttributeName": "window_job_id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print("Table is active.")
    return table


def seed_items(table):
    inserted = 0
    write_request_units = Decimal("0")
    for item in SAMPLE_JOB_REQUESTS:
        response = table.put_item(
            Item=item,
            ConditionExpression=(
                "attribute_not_exists(batch_date) "
                "AND attribute_not_exists(window_job_id)"
            ),
            ReturnConsumedCapacity="TOTAL",
        )
        write_request_units += Decimal(
            str(response.get("ConsumedCapacity", {}).get("CapacityUnits", 0))
        )
        inserted += 1
    return inserted, write_request_units


def main():
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = create_table_if_needed(dynamodb)

    try:
        inserted, write_request_units = seed_items(table)
        request_cost = ddb_write_cost(write_request_units)
        print(f"Inserted {inserted} job request records into {TABLE_NAME}.")
        print(
            "DynamoDB write request units: "
            f"{write_request_units} | raw request cost: {money(request_cost)}"
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            print("Sample records already exist. No new rows were inserted.")
        else:
            raise


if __name__ == "__main__":
    main()
