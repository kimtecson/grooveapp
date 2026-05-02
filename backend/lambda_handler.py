"""
lambda_handler.py
Wraps the Flask app for AWS Lambda + API Gateway (proxy integration).
Uses aws-wsgi to translate API Gateway events into WSGI calls.

Deploy: zip this file + app.py + requirements (installed locally) → Lambda
"""

import awsgi
from app import app


def handler(event, context):
    return awsgi.response(app, event, context, base64_content_types={"image/png", "image/jpeg"})
