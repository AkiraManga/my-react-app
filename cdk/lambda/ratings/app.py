import boto3
import json
import os
import time
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
ratings_table = dynamodb.Table(os.environ["RATINGS_TABLE"])

# Encoder per serializzare Decimal in JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0:
                return int(o)
            else:
                return float(o)
        return super(DecimalEncoder, self).default(o)

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
        },
        "body": json.dumps(body, cls=DecimalEncoder),
    }

def handler(event, context):
    print("Evento ricevuto:", json.dumps(event))

    http_method = event.get("httpMethod", "")

    # Risposta al preflight CORS
    if http_method == "OPTIONS":
        return response(200, {"message": "CORS preflight OK"})

    # ---------------- POST /ratings/{album_id} ----------------
    if http_method == "POST":
        try:
            body = json.loads(event.get("body", "{}"))
            album_id = event.get("pathParameters", {}).get("album_id")

            if not album_id:
                return response(400, {"error": "Missing album_id"})

            claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
            user_id = claims.get("sub")

            if not user_id:
                return response(401, {"error": "Unauthorized: missing user_id"})

            rating = body.get("rating")
            if rating is None:
                return response(400, {"error": "Missing rating"})

            comment = body.get("comment") or body.get("review_text", "")

            item = {
                "album_id": album_id,   # PK
                "user_id": user_id,     # SK
                "timestamp": int(time.time()),
                "rating": int(rating),
                "comment": comment,
            }

            ratings_table.put_item(Item=item)

            return response(201, {"message": "Review saved", "item": item})

        except Exception as e:
            print("Errore durante POST:", str(e))
            return response(500, {"error": str(e)})

    # ---------------- GET /ratings/{album_id} ----------------
    if http_method == "GET":
        try:
            album_id = event.get("pathParameters", {}).get("album_id")
            if not album_id:
                return response(400, {"error": "Missing album_id"})

            # Query tutte le recensioni per album
            result = ratings_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("album_id").eq(album_id)
            )

            return response(200, {"reviews": result.get("Items", [])})

        except Exception as e:
            print("Errore durante GET:", str(e))
            return response(500, {"error": str(e)})

    return response(405, {"error": f"Method {http_method} not allowed"})
