"""
Music Subscription App - Flask Backend
Token-based auth using sessionStorage (avoids cross-origin cookie issues in dev).
The token is the user's email stored in sessionStorage and sent as X-User-Email header.
"""

import os
import boto3
from flask import Flask, request, jsonify
from flask_cors import CORS
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from functools import wraps
from urllib.parse import unquote

app = Flask(__name__)

CORS(app, supports_credentials=True, origins=["*"])

# ── AWS config ────────────────────────────────────────────────────────────────
AWS_REGION        = os.environ.get("AWS_REGION",        "us-east-1")
S3_BUCKET         = os.environ.get("S3_BUCKET",         "music-app-images")
LOGIN_TABLE       = os.environ.get("LOGIN_TABLE",        "login")
MUSIC_TABLE       = os.environ.get("MUSIC_TABLE",        "music")
SUB_TABLE         = os.environ.get("SUB_TABLE",          "subscription")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT",  None)

dynamo_kwargs = {"region_name": AWS_REGION}
if DYNAMODB_ENDPOINT:
    dynamo_kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
    print(f"[DEV] Using local DynamoDB at {DYNAMODB_ENDPOINT}")

dynamodb  = boto3.resource("dynamodb", **dynamo_kwargs)
s3_client = boto3.client("s3", region_name=AWS_REGION)

login_table = dynamodb.Table(LOGIN_TABLE)
music_table = dynamodb.Table(MUSIC_TABLE)
sub_table   = dynamodb.Table(SUB_TABLE)


# ── Auth: read email from header (set by frontend after login) ────────────────
def get_current_user():
    return request.headers.get("X-User-Email", "").strip().lower()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ── Helper: presigned S3 URL ──────────────────────────────────────────────────
# Simple in-memory cache for presigned URLs
url_cache = {}

def presigned_url(artist: str) -> str:
    if DYNAMODB_ENDPOINT:
        return ""

    # Check cache first
    if artist in url_cache:
        return url_cache[artist]

    key = artist.replace(" ", "").replace("&", "").replace(".", "") + ".jpg"
    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=900,
        )
        url_cache[artist] = url
        return url
    except Exception:
        url_cache[artist] = ""
        return ""


# ── Auth routes ───────────────────────────────────────────────────────────────
@app.route("/auth/login", methods=["POST"])
def login():
    data     = request.get_json(force=True)
    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "email or password is invalid"}), 400

    try:
        resp = login_table.get_item(Key={"email": email})
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

    item = resp.get("Item")
    if not item or item.get("password") != password:
        return jsonify({"error": "email or password is invalid"}), 401

    return jsonify({"message": "Login successful", "email": email, "user_name": item.get("user_name", "")}), 200


@app.route("/auth/register", methods=["POST"])
def register():
    data      = request.get_json(force=True)
    email     = (data.get("email")     or "").strip().lower()
    user_name = (data.get("user_name") or "").strip()
    password  = (data.get("password")  or "").strip()

    if not email or not user_name or not password:
        return jsonify({"error": "All fields are required"}), 400

    try:
        resp = login_table.get_item(Key={"email": email})
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

    if resp.get("Item"):
        return jsonify({"error": "The email already exists"}), 409

    try:
        login_table.put_item(Item={"email": email, "user_name": user_name, "password": password})
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Registration successful"}), 201


@app.route("/auth/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logged out"}), 200


@app.route("/auth/me", methods=["GET"])
@login_required
def me():
    email = get_current_user()
    try:
        resp = login_table.get_item(Key={"email": email})
    except ClientError as e:
        return jsonify({"error": str(e)}), 500
    item = resp.get("Item")
    if not item:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"email": email, "user_name": item.get("user_name", "")}), 200


# ── Music query ───────────────────────────────────────────────────────────────
@app.route("/music/query", methods=["GET"])
@login_required
def query_music():
    title  = (request.args.get("title")  or "").strip().lower()
    artist = (request.args.get("artist") or "").strip().lower()
    year   = (request.args.get("year")   or "").strip()
    album  = (request.args.get("album")  or "").strip().lower()

    if not any([title, artist, year, album]):
        return jsonify({"error": "At least one field must be provided"}), 400

    try:
        resp = music_table.scan()
        all_items = resp.get("Items", [])

    except ClientError as e:
        return jsonify({"error": str(e)}), 500

    results = []
    for item in all_items:
        if artist and artist not in item.get("artist", "").lower():
            continue
        if title and title not in item.get("title", "").lower():
            continue
        if album and album not in item.get("album", "").lower():
            continue
        if year and year != item.get("year", ""):
            continue
        results.append(item)

    for item in results:
        item["img_url"] = presigned_url(item.get("artist", "")) or item.get("image_url", "")

    if not results:
        return jsonify({"message": "No result is retrieved. Please query again", "songs": []}), 200

    return jsonify({"songs": results}), 200


# ── Subscription routes ───────────────────────────────────────────────────────
@app.route("/subscription", methods=["GET"])
@login_required
def get_subscriptions():
    email = get_current_user()
    try:
        resp  = sub_table.query(KeyConditionExpression=Key("email").eq(email))
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

    items = resp.get("Items", [])
    for item in items:
        item["img_url"] = presigned_url(item.get("artist", "")) or item.get("image_url", "")
    return jsonify({"subscriptions": items}), 200

@app.route("/subscription", methods=["POST"])
@login_required
def add_subscription():
    email  = get_current_user()
    data   = request.get_json(force=True)
    title     = (data.get("title")     or "").strip()
    artist    = (data.get("artist")    or "").strip()
    year      = str(data.get("year")   or "").strip()
    album     = (data.get("album")     or "").strip()
    image_url = (data.get("image_url") or "").strip()

    if not all([title, artist, year, album]):
        return jsonify({"error": "Missing song fields"}), 400

    music_id = f"{artist}#{title}#{year}#{album}"
    try:
        sub_table.put_item(Item={"email": email, "music_id": music_id,
                                  "title": title, "artist": artist, "year": year, "album": album,
                                  "image_url": image_url})
    except ClientError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Subscribed successfully"}), 201

@app.route("/subscription/<path:music_id>", methods=["DELETE"])
@login_required
def remove_subscription(music_id):
    email = get_current_user()
    # DECODE the URL-encoded parameter
    music_id = unquote(music_id)
    try:
        response = sub_table.delete_item(
            Key={
                "email": email,
                "music_id": music_id
            },
            ReturnValues="ALL_OLD"
        )

        if response.get('Attributes'):
            print(f"Successfully deleted: {response['Attributes']}")
            return jsonify({"message": "Subscription removed"}), 200
        else:
            print(f"No item found: email={email}, music_id={music_id}")
            return jsonify({"error": "Subscription not found"}), 404

    except ClientError as e:
        print(f"DynamoDB error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
