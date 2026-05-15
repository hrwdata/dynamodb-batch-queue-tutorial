import argparse
import os

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = "db_batch_window_requests"
REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


def delete_table(table_name: str, wait: bool):
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(table_name)
    table.delete()
    if wait:
        table.wait_until_not_exists()
    print(f"Deleted DynamoDB table: {table_name}")


def delete_stack(stack_name: str):
    cloudformation = boto3.client("cloudformation", region_name=REGION)
    cloudformation.delete_stack(StackName=stack_name)
    print(f"Started CloudFormation stack deletion: {stack_name}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table-name", default=TABLE_NAME)
    parser.add_argument("--stack-name")
    parser.add_argument("--no-wait", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        if args.stack_name:
            delete_stack(args.stack_name)
        else:
            delete_table(args.table_name, wait=not args.no_wait)
    except ClientError as exc:
        print(exc)
        raise


if __name__ == "__main__":
    main()
