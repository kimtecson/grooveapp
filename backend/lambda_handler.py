"""
lambda_handler.py
Wraps the Flask app for AWS Lambda + API Gateway (proxy integration).
Uses aws-wsgi to translate API Gateway events into WSGI calls.

Deploy: zip this file + app.py + requirements (installed locally) → Lambda
"""

import awsgi
from Backend.app import app


def handler(event, context):
    """
    AWS Lambda entry point.
    API Gateway (HTTP API or REST API with proxy integration) sends events here.
    aws-wsgi translates the event → WSGI environ → Flask → response dict.
    """
    return awsgi.response(app, event, context, base64_content_types={"image/png", "image/jpeg"})
