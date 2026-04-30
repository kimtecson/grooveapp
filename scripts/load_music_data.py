"""
load_music_data.py
Loads all songs from 2026a2_songs.json into the DynamoDB music table.

Key design: composite SK = title#year#album ensures every row is unique,
including re-releases (e.g. "Delicate" by Taylor Swift appears twice with
different album names, "Rivers of Babylon" by The Melodians appears in 1970
and 2003). No songs are overwritten.

Usage:
    python load_music_data.py
    python load_music_data.py --json path/to/2026a2_songs.json
"""

import json
import argparse
import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

AWS_REGION        = os.environ.get("AWS_REGION",        "us-east-1")
MUSIC_TABLE       = os.environ.get("MUSIC_TABLE",        "music")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT",  None)
JSON_FILE         = "2026a2_songs.json"

kwargs = {"region_name": AWS_REGION}
if DYNAMODB_ENDPOINT:
    kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
    print(f"[DEV] Using local DynamoDB at {DYNAMODB_ENDPOINT}")

dynamodb = boto3.resource("dynamodb", **kwargs)


def load_songs(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    songs = data.get("songs", [])
    print(f"Found {len(songs)} songs in '{json_path}'")

    table      = dynamodb.Table(MUSIC_TABLE)
    loaded     = 0
    duplicates = 0

    # Use batch_writer for efficiency (auto-flushes in batches of 25)
    with table.batch_writer() as batch:
        seen = set()
        for song in songs:
            title  = song.get("title",    "").strip()
            artist = song.get("artist",   "").strip()
            year   = str(song.get("year", "")).strip()
            album  = song.get("album",    "").strip()
            img    = song.get("img_url",  "").strip()

            if not title or not artist:
                print(f"  SKIP (missing fields): {song}")
                continue

            # Composite sort key — guarantees uniqueness across all edge cases
            sk = f"{title}#{year}#{album}"

            dedup_key = (artist, sk)
            if dedup_key in seen:
                print(f"  DUPLICATE skipped: {artist} | {sk}")
                duplicates += 1
                continue
            seen.add(dedup_key)

            batch.put_item(Item={
                "artist":           artist,
                "title#year#album": sk,
                "title":            title,
                "year":             year,
                "album":            album,
                "image_url":        img,
            })
            loaded += 1

    print(f"\nSummary:")
    print(f"  Loaded    : {loaded}")
    print(f"  Duplicates: {duplicates}")
    print(f"  Total     : {len(songs)}")

    # Quick verification — spot check a few artists
    print("\nVerification spot-checks:")
    for artist in ["Taylor Swift", "Jimmy Buffett", "The Melodians", "Sublime"]:
        resp  = table.query(KeyConditionExpression=Key("artist").eq(artist))
        count = resp.get("Count", 0)
        print(f"  {artist}: {count} song(s) in table")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=JSON_FILE, help="Path to 2026a2_songs.json")
    args = parser.parse_args()
    load_songs(args.json)
