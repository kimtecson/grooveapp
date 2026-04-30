"""
upload_images_s3.py
Downloads all unique artist images from the img_url values in 2026a2_songs.json
and uploads them to an S3 bucket.

The S3 key matches the filename from the URL (e.g. TomPetty.jpg).
Objects are stored as private — the Flask app generates presigned URLs for access.

Usage:
    python upload_images_s3.py --bucket your-bucket-name
    python upload_images_s3.py --bucket your-bucket-name --json path/to/2026a2_songs.json
"""

import json
import argparse
import os
import urllib.request
import urllib.error
import boto3
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"
JSON_FILE  = "2026a2_songs.json"


def create_bucket_if_missing(s3, bucket: str, region: str):
    """Create the S3 bucket if it doesn't already exist."""
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"  Bucket '{bucket}' already exists.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            print(f"  Creating bucket '{bucket}'...")
            if region == "us-east-1":
                # us-east-1 must NOT specify LocationConstraint
                s3.create_bucket(Bucket=bucket)
            else:
                s3.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
            # Block all public access — images served via presigned URLs only
            s3.put_public_access_block(
                Bucket=bucket,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls":       True,
                    "IgnorePublicAcls":      True,
                    "BlockPublicPolicy":     True,
                    "RestrictPublicBuckets": True,
                },
            )
            print(f"  Bucket '{bucket}' created with public access blocked.")
        else:
            raise


def upload_images(json_path: str, bucket: str, region: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    songs = data.get("songs", [])

    # Collect unique image URLs
    urls = {}
    for song in songs:
        url = song.get("img_url", "").strip()
        if url:
            key = url.rsplit("/", 1)[-1]   # e.g. "TomPetty.jpg"
            urls[key] = url

    print(f"Found {len(urls)} unique artist images to upload.")

    s3 = boto3.client("s3", region_name=region)
    create_bucket_if_missing(s3, bucket, region)

    uploaded  = 0
    skipped   = 0
    failed    = 0
    tmp_dir   = "/tmp/groove_images"
    os.makedirs(tmp_dir, exist_ok=True)

    for key, url in urls.items():
        tmp_path = os.path.join(tmp_dir, key)

        # Check if already in S3 to avoid re-uploading
        try:
            s3.head_object(Bucket=bucket, Key=key)
            print(f"  SKIP (already in S3): {key}")
            skipped += 1
            continue
        except ClientError:
            pass   # doesn't exist yet — proceed

        # Download
        try:
            print(f"  Downloading: {url}")
            urllib.request.urlretrieve(url, tmp_path)
        except urllib.error.URLError as e:
            print(f"  FAIL (download): {key} — {e}")
            failed += 1
            continue

        # Upload
        try:
            content_type = "image/jpeg" if key.lower().endswith(".jpg") else "image/png"
            s3.upload_file(
                tmp_path,
                bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            print(f"  Uploaded: s3://{bucket}/{key}")
            uploaded += 1
        except ClientError as e:
            print(f"  FAIL (upload): {key} — {e}")
            failed += 1
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    print(f"\nSummary:")
    print(f"  Uploaded : {uploaded}")
    print(f"  Skipped  : {skipped}")
    print(f"  Failed   : {failed}")
    print(f"\nImages stored at: s3://{bucket}/")
    print("Access via presigned URLs — bucket is NOT publicly accessible.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--json",   default=JSON_FILE, help="Path to 2026a2_songs.json")
    parser.add_argument("--region", default=AWS_REGION, help="AWS region")
    args = parser.parse_args()

    upload_images(args.json, args.bucket, args.region)
