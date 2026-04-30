"""
create_subscription_table.py
Creates the DynamoDB subscription table.
Run once before starting the app.

Usage:
    python create_subscription_table.py
"""

import boto3
import os
from botocore.exceptions import ClientError

AWS_REGION        = os.environ.get("AWS_REGION",        "us-east-1")
SUB_TABLE         = os.environ.get("SUB_TABLE",          "subscription")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT",  None)

kwargs = {"region_name": AWS_REGION}
if DYNAMODB_ENDPOINT:
    kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
    print(f"[DEV] Using local DynamoDB at {DYNAMODB_ENDPOINT}")

client = boto3.client("dynamodb", **kwargs)


def create_table():
    print(f"Creating table '{SUB_TABLE}'...")
    try:
        client.create_table(
            TableName=SUB_TABLE,
            KeySchema=[
                {"AttributeName": "email",    "KeyType": "HASH"},
                {"AttributeName": "music_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "email",    "AttributeType": "S"},
                {"AttributeName": "music_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        waiter = client.get_waiter("table_exists")
        waiter.wait(TableName=SUB_TABLE)
        print(f"  Table '{SUB_TABLE}' created successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table '{SUB_TABLE}' already exists — skipping creation.")
        else:
            raise


if __name__ == "__main__":
    create_table()
