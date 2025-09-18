import os
import json
import urllib.parse
import urllib.request

COGNITO_DOMAIN = os.environ["COGNITO_DOMAIN"]
CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
REDIRECT_URI = os.environ["REDIRECT_URI"]

def handler(event, context):
    try:
        # Recupera il "code" dalla query string
        code = event.get("queryStringParameters", {}).get("code")
        if not code:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing code"})
            }

        # Endpoint token Cognito
        token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"

        # Parametri
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
        encoded_data = urllib.parse.urlencode(data).encode("utf-8")

        # Richiesta POST a Cognito
        req = urllib.request.Request(
            token_url,
            data=encoded_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            status = resp.getcode()

        return {
            "statusCode": status,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": body
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
