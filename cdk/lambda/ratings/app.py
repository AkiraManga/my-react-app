import boto3
import json
import os
import time
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
ratings_table = dynamodb.Table(os.environ["RATINGS_TABLE"])
albums_table = dynamodb.Table(os.environ["ALBUMS_TABLE"])
users_table = dynamodb.Table(os.environ["USERS_TABLE"])

sns = boto3.client("sns")   # 👈 client SNS
TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]  # 👈 lo passi come variabile ambiente


# Encoder per serializzare Decimal in JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
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
    resource_path = event.get("resource", "")

    # Risposta al preflight CORS
    if http_method == "OPTIONS":
        return response(200, {"message": "CORS preflight OK"})

    # ---------------- POST /ratings/{album_id} (recensione) ----------------
    if http_method == "POST" and not resource_path.endswith("like"):
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
                "timestamp": int(time.time() * 1000),   # millisecondi
                "rating": int(rating),
                "comment": comment,
                "likes": 0,
                "liked_by": [],   # 👈 inizializzo array vuoto
            }

            # Salva la recensione nella tabella Ratings
            ratings_table.put_item(Item=item)

            # Recupera i valori attuali dell'album
            album = albums_table.get_item(Key={"album_id": album_id}).get("Item", {})
            old_count = int(album.get("ratings_count", 0))
            old_avg = float(album.get("average_rating", 0))

            # Calcola i nuovi valori
            new_count = old_count + 1
            new_avg = ((old_avg * old_count) + int(rating)) / new_count

            # Aggiorna l'album
            albums_table.update_item(
                Key={"album_id": album_id},
                UpdateExpression="SET ratings_count = :c, average_rating = :a",
                ExpressionAttributeValues={
                    ":c": Decimal(new_count),
                    ":a": Decimal(str(new_avg))
                }
            )

            return response(201, {"message": "Review saved", "item": item})

        except Exception as e:
            print("Errore durante POST recensione:", str(e))
            return response(500, {"error": str(e)})

    # ---------------- POST /ratings/{album_id}/{review_user_id}/like ----------------
    if http_method == "POST" and resource_path.endswith("like"):
        try:
            album_id = event.get("pathParameters", {}).get("album_id")
            review_user_id = event.get("pathParameters", {}).get("review_user_id")

            if not album_id or not review_user_id:
                return response(400, {"error": "Missing album_id or review_user_id"})

            claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
            liker_id = claims.get("sub")
            liker_email = claims.get("email", "")

            if not liker_id:
                return response(401, {"error": "Unauthorized: missing liker user_id"})

            try:
                # Incrementa likes solo se l’utente non ha già messo like
                ratings_table.update_item(
                    Key={"album_id": album_id, "user_id": review_user_id},
                    UpdateExpression="""
                        ADD likes :inc 
                        SET liked_by = list_append(if_not_exists(liked_by, :empty), :u)
                    """,
                    ConditionExpression="attribute_not_exists(liked_by) OR not contains(liked_by, :liker)",
                    ExpressionAttributeValues={
                        ":inc": 1,
                        ":u": [liker_id],
                        ":empty": [],
                        ":liker": liker_id,
                    },
                    ReturnValues="UPDATED_NEW"
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    return response(409, {"error": "Hai già messo like a questo commento"})
                else:
                    raise

            # Recupera email autore commento
            user_item = users_table.get_item(Key={"user_id": review_user_id}).get("Item", {})
            to_email = user_item.get("email")

            if to_email:
                sns.publish(
                    TopicArn=TOPIC_ARN,
                    Subject="Nuovo like al tuo commento",
                    Message=f"Hai ricevuto un like da {liker_email} sul tuo commento all'album {album_id}!"
                )

            return response(200, {"message": "Like registrato"})

        except Exception as e:
            print("Errore durante LIKE:", str(e))
            return response(500, {"error": str(e)})

    # ---------------- GET /ratings/{album_id} ----------------
    if http_method == "GET":
        try:
            album_id = event.get("pathParameters", {}).get("album_id")
            if not album_id:
                return response(400, {"error": "Missing album_id"})

            # Query tutte le recensioni per album, ordinate dal più recente
            result = ratings_table.query(
                KeyConditionExpression=Key("album_id").eq(album_id),
                ScanIndexForward=False
            )

            items = result.get("Items", [])
            for i in items:
                if "likes" not in i:
                    i["likes"] = 0

            # Calcola media e conteggio
            count = len(items)
            avg = sum(int(i["rating"]) for i in items) / count if count > 0 else 0

            return response(200, {
                "reviews": items,
                "ratings_count": count,
                "average_rating": avg
            })

        except Exception as e:
            print("Errore durante GET:", str(e))
            return response(500, {"error": str(e)})

    return response(405, {"error": f"Method {http_method} not allowed"})
