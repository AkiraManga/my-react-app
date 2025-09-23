import json
import boto3
import os
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["USERS_TABLE"])

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
        },
        "body": json.dumps(body)
    }

def handler(event, context):
    print("Event:", json.dumps(event))

    http_method = event.get("httpMethod")
    path = event.get("path", "")

    # Path params
    path_params = event.get("pathParameters") or {}

    # Recupero user_id dal token Cognito
    claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
    user_id = claims.get("sub")
    email = claims.get("email")

    if not user_id:
        return response(401, {"error": "Unauthorized"})

    # POST /users/favorites/{album_id}
    if http_method == "POST" and path_params.get("album_id"):
        album_id = path_params["album_id"]

        # Se utente non esiste ancora (fallback), lo creo
        try:
            table.put_item(
                Item={"user_id": user_id, "email": email, "favorites": set()},
                ConditionExpression="attribute_not_exists(user_id)"
            )
            print(f"Created user {user_id}")
        except Exception as e:
            print("User already exists or error:", e)

        # Aggiorno i preferiti
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="ADD favorites :a",
            ExpressionAttributeValues={":a": set([album_id])},
        )

        return response(200, {"message": f"Album {album_id} aggiunto ai preferiti"})

    return response(400, {"error": "Bad request"})
