"""
create_music_table.py
Creates the DynamoDB music table with:
  - PK:  artist (String)
  - SK:  title#year#album (String)  ← composite, guarantees uniqueness
  - GSI: title-index       (PK=title,  SK=artist)  ← title-only queries
  - LSI: artist-year-index (PK=artist, SK=year)    ← artist + year queries

Run once before loading song data.

Usage:
    python create_music_table.py
"""

import os
import boto3
from botocore.exceptions import ClientError

AWS_REGION        = os.environ.get("AWS_REGION",        "us-east-1")
MUSIC_TABLE       = os.environ.get("MUSIC_TABLE",        "music")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT",  None)

kwargs = {"region_name": AWS_REGION}
if DYNAMODB_ENDPOINT:
    kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
    print(f"[DEV] Using local DynamoDB at {DYNAMODB_ENDPOINT}")

client = boto3.client("dynamodb", **kwargs)


def create_table():
    print(f"Creating table '{MUSIC_TABLE}'...")
    try:
        client.create_table(
            TableName=MUSIC_TABLE,
            # ── Key schema ────────────────────────────────────────────────────
            KeySchema=[
                {"AttributeName": "artist",           "KeyType": "HASH"},
                {"AttributeName": "music_sk",         "KeyType": "RANGE"},
            ],
            # ── All attributes referenced in keys / indexes ───────────────────
            AttributeDefinitions=[
                {"AttributeName": "artist",           "AttributeType": "S"},
                {"AttributeName": "music_sk",         "AttributeType": "S"},
                {"AttributeName": "title",            "AttributeType": "S"},
                {"AttributeName": "artist_year_sk",   "AttributeType": "S"},
                {"AttributeName": "title_lookup_sk",  "AttributeType": "S"},
            ],
            # ── GSI: query by title ───────────────────────────────────────────
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "music_GSI_title",
                    "KeySchema": [
                        {"AttributeName": "title",           "KeyType": "HASH"},
                        {"AttributeName": "title_lookup_sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            # ── LSI: query by artist + year ───────────────────────────────────
            LocalSecondaryIndexes=[
                {
                    "IndexName": "music_LSI_artist_year",
                    "KeySchema": [
                        {"AttributeName": "artist",         "KeyType": "HASH"},
                        {"AttributeName": "artist_year_sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Wait until active
        waiter = client.get_waiter("table_exists")
        waiter.wait(TableName=MUSIC_TABLE)
        print(f"  Table '{MUSIC_TABLE}' created successfully.")
        print(f"  PK  : artist")
        print(f"  SK  : music_sk = album#year#title")
        print(f"  GSI : music_GSI_title       (PK=title,  SK=title_lookup_sk=artist#album#year)")
        print(f"  LSI : music_LSI_artist_year (PK=artist, SK=artist_year_sk=year#album#title)")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  Table '{MUSIC_TABLE}' already exists — skipping creation.")
        else:
            raise


if __name__ == "__main__":
    create_table()
