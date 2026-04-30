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
    {"email": "s3958264@student.rmit.edu.au", "user_name": "Kimberly Tecson",  "password": "Password01!"},
    {"email": "s3910432@student.rmit.edu.au", "user_name": "James Miller",     "password": "Password02!"},
    {"email": "s3821765@student.rmit.edu.au", "user_name": "Priya Sharma",     "password": "Password03!"},
    {"email": "s3745890@student.rmit.edu.au", "user_name": "Lucas Nguyen",     "password": "Password04!"},
    {"email": "s3698123@student.rmit.edu.au", "user_name": "Aisha Patel",      "password": "Password05!"},
    {"email": "s3612457@student.rmit.edu.au", "user_name": "Connor Walsh",     "password": "Password06!"},
    {"email": "s3589034@student.rmit.edu.au", "user_name": "Sofia Rossi",      "password": "Password07!"},
    {"email": "s3476291@student.rmit.edu.au", "user_name": "Daniel Kim",       "password": "Password08!"},
    {"email": "s3354678@student.rmit.edu.au", "user_name": "Emma Thompson",    "password": "Password09!"},
    {"email": "s3231045@student.rmit.edu.au", "user_name": "Mohammed Al-Amin", "password": "Password10!"},
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
