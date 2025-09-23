import json
import boto3
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["USERS_TABLE"])

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST,DELETE,PUT"
        },
        "body": json.dumps(body)
    }

def handler(event, context):
    print("Event:", json.dumps(event))  # log completo per debug
    http_method = event.get("httpMethod")
    path_params = event.get("pathParameters") or {}

    # ✅ Gestione preflight CORS
    if http_method == "OPTIONS":
        return response(200, {"message": "CORS preflight"})

    # ✅ Recupero user_id dal token Cognito
    claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
    user_id = claims.get("sub")
    email = claims.get("email")

    if not user_id:
        return response(401, {"error": "Unauthorized"})

    # ✅ POST /users/favorites/{album_id}
    if http_method == "POST" and "album_id" in path_params:
        album_id = path_params["album_id"]
        print(f"Aggiungo album {album_id} ai preferiti di {user_id}")

        # Se l’utente non esiste ancora → lo creo SENZA favorites
        try:
            table.put_item(
                Item={"user_id": user_id, "email": email},
                ConditionExpression="attribute_not_exists(user_id)"
            )
            print(f"Creato nuovo utente {user_id} in DynamoDB")
        except Exception as e:
            print(f"Utente già esistente o errore su put_item: {str(e)}")

        # Aggiorna i preferiti con ADD su String Set
        try:
            table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="ADD favorites :a",
                ExpressionAttributeValues={":a": set([album_id])}
            )
            print(f"Album {album_id} aggiunto ai preferiti di {user_id}")
        except Exception as e:
            print(f"Errore in update_item: {str(e)}")
            return response(500, {"error": "Errore aggiornando i preferiti"})

        return response(200, {"message": f"Album {album_id} aggiunto ai preferiti"})

    return response(400, {"error": "Bad request"})
