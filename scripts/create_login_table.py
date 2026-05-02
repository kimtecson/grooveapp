"""
create_login_table.py
Creates the DynamoDB login table and populates it with 10 users.
Run once before starting the app.

Usage:
    python create_login_table.py
"""

import boto3
import os
from botocore.exceptions import ClientError

AWS_REGION        = os.environ.get("AWS_REGION",        "us-east-1")
LOGIN_TABLE       = os.environ.get("LOGIN_TABLE",        "login")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT",  None)

kwargs = {"region_name": AWS_REGION}
if DYNAMODB_ENDPOINT:
    kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
    print(f"[DEV] Using local DynamoDB at {DYNAMODB_ENDPOINT}")

dynamodb = boto3.resource("dynamodb", **kwargs)
client   = boto3.client("dynamodb",   **kwargs)

# ── 10 seed users ─────────────────────────────────────────────────────────────
USERS = [
    {"email": "s41599720@student.rmit.edu.au", "user_name": "KimberlyTecson0", "password": "012345"},
    {"email": "s41599721@student.rmit.edu.au", "user_name": "KimberlyTecson1", "password": "123456"},
    {"email": "s41599722@student.rmit.edu.au", "user_name": "KimberlyTecson2", "password": "234567"},
    {"email": "s41599723@student.rmit.edu.au", "user_name": "KimberlyTecson3", "password": "345678"},
    {"email": "s41599724@student.rmit.edu.au", "user_name": "KimberlyTecson4", "password": "456789"},
    {"email": "s41599725@student.rmit.edu.au", "user_name": "KimberlyTecson5", "password": "567890"},
    {"email": "s41599726@student.rmit.edu.au", "user_name": "KimberlyTecson6", "password": "678901"},
    {"email": "s41599727@student.rmit.edu.au", "user_name": "KimberlyTecson7", "password": "789012"},
    {"email": "s41599728@student.rmit.edu.au", "user_name": "KimberlyTecson8", "password": "890123"},
    {"email": "s41599729@student.rmit.edu.au", "user_name": "KimberlyTecson9", "password": "901234"},
]


def create_table():
    print(f"Creating table '{LOGIN_TABLE}'...")
    try:
        table = client.create_table(
            TableName=LOGIN_TABLE,
            KeySchema=[
                {"AttributeName": "email", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        # Wait until table is active
        waiter = client.get_waiter("table_exists")
        waiter.wait(TableName=LOGIN_TABLE)
        print(f"  Table '{LOGIN_TABLE}' created successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table '{LOGIN_TABLE}' already exists — skipping creation.")
        else:
            raise


def load_users():
    table = dynamodb.Table(LOGIN_TABLE)
    print(f"Loading {len(USERS)} users...")
    for user in USERS:
        table.put_item(Item=user)
        print(f"  Inserted: {user['email']} ({user['user_name']})")
    print("Done.")


if __name__ == "__main__":
    create_table()
    load_users()
