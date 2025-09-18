import os
import json
import requests

def handler(event, context):
    code = event["queryStringParameters"].get("code")

    token_url = f"https://{os.environ['COGNITO_DOMAIN']}/oauth2/token"
    redirect_uri = os.environ["REDIRECT_URI"]

    data = {
        "grant_type": "authorization_code",
        "client_id": os.environ["COGNITO_CLIENT_ID"],
        "code": code,
        "redirect_uri": redirect_uri
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=data, headers=headers)

    return {
        "statusCode": response.status_code,
        "headers": {"Content-Type": "application/json"},
        "body": response.text
    }
